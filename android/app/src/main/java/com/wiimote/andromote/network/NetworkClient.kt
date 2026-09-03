package com.wiimote.andromote.network

import android.content.Context
import android.os.Build
import android.os.Looper
import android.util.Log
import com.wiimote.andromote.model.ConnectionState
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import org.json.JSONObject
import java.io.DataInputStream
import java.io.DataOutputStream
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.Socket
import java.util.UUID

class NetworkClient(private val context: Context) {

    private val tag = "NetworkClient"

    private val _connectionState = MutableStateFlow(ConnectionState())
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

    private val clientScope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    private var tcpSocket: Socket? = null
    private var dataIn: DataInputStream? = null
    private var dataOut: DataOutputStream? = null

    private var udpSocket: DatagramSocket? = null
    private var serverInetAddress: InetAddress? = null
    private var udpMotionPort: Int = 42426

    private var pingJob: Job? = null
    private var readJob: Job? = null

    private var sequenceNumber: Short = 0
    private var lastPingSentMs: Long = 0
    private var lastRttMs: Float = 0f

    private val prefs = context.getSharedPreferences("andromote_client", Context.MODE_PRIVATE)

    val deviceId: String
        get() {
            var id = prefs.getString("device_id", null)
            if (id == null) {
                id = UUID.randomUUID().toString()
                prefs.edit().putString("device_id", id).apply()
            }
            return id
        }

    val deviceName: String
        get() = "${Build.MANUFACTURER} ${Build.MODEL}"

    fun connect(host: String, tcpPort: Int = 42425, motionPort: Int = 42426, pin: String? = null) {
        disconnect()

        _connectionState.value = ConnectionState(
            isConnecting = true,
            serverIp = host
        )

        clientScope.launch {
            try {
                Log.d(tag, "Connecting to TCP $host:$tcpPort...")
                val socket = Socket(host, tcpPort)
                socket.tcpNoDelay = true
                socket.soTimeout = 10000

                tcpSocket = socket
                dataIn = DataInputStream(socket.getInputStream())
                dataOut = DataOutputStream(socket.getOutputStream())

                // Init UDP motion socket
                udpMotionPort = motionPort
                serverInetAddress = InetAddress.getByName(host)
                udpSocket = DatagramSocket()

                // Start read loop
                startTcpReadLoop()

                // Send Hello handshake
                sendTcpMessage(ProtocolPackets.createHello(deviceId))

                val savedToken = prefs.getString("auth_token_$host", null)
                if (pin != null) {
                    sendTcpMessage(ProtocolPackets.createPair(pin, deviceId, deviceName))
                } else if (savedToken != null) {
                    sendTcpMessage(ProtocolPackets.createAuth(savedToken, deviceId, deviceName))
                }

                // Start periodic ping loop
                startPingLoop()

            } catch (e: Exception) {
                Log.e(tag, "Connection error: ${e.message}")
                disconnect()
                _connectionState.value = ConnectionState(
                    errorMessage = "Failed to connect: ${e.message}"
                )
            }
        }
    }

    fun submitPin(pin: String) {
        clientScope.launch {
            sendTcpMessage(ProtocolPackets.createPair(pin, deviceId, deviceName))
        }
    }

    fun disconnect() {
        pingJob?.cancel()
        readJob?.cancel()

        try {
            tcpSocket?.close()
        } catch (e: Exception) {}
        tcpSocket = null
        dataIn = null
        dataOut = null

        try {
            udpSocket?.close()
        } catch (e: Exception) {}
        udpSocket = null

        _connectionState.value = ConnectionState()
    }

    fun sendButton(button: String, state: String) {
        if (!_connectionState.value.isConnected) return
        clientScope.launch {
            sendTcpMessage(ProtocolPackets.createButton(button, state, System.currentTimeMillis()))
        }
    }

    fun sendRecenter() {
        if (!_connectionState.value.isConnected) return
        clientScope.launch {
            sendTcpMessage(ProtocolPackets.createRecenter())
        }
    }

    fun sendMotion(qx: Float, qy: Float, qz: Float, qw: Float,
                   gx: Float, gy: Float, gz: Float,
                   ax: Float, ay: Float, az: Float,
                   timestampMs: Long) {
        if (!_connectionState.value.isConnected) return

        val socket = udpSocket ?: return
        val targetAddr = serverInetAddress ?: return

        val sendBlock = {
            try {
                sequenceNumber = (sequenceNumber + 1).toShort()
                val packetData = ProtocolPackets.packBinaryMotion(
                    sequenceNumber, timestampMs,
                    qx, qy, qz, qw,
                    gx, gy, gz,
                    ax, ay, az
                )
                val packet = DatagramPacket(packetData, packetData.size, targetAddr, udpMotionPort)
                socket.send(packet)
            } catch (e: Exception) {
                Log.d(tag, "UDP send error: ${e.message}")
            }
        }

        if (Looper.myLooper() == Looper.getMainLooper()) {
            clientScope.launch(Dispatchers.IO) {
                sendBlock()
            }
        } else {
            sendBlock()
        }
    }

    private fun sendTcpMessage(jsonStr: String) {
        val out = dataOut ?: return
        try {
            synchronized(out) {
                val bytes = jsonStr.toByteArray(Charsets.UTF_8)
                out.writeInt(bytes.size)
                out.write(bytes)
                out.flush()
            }
        } catch (e: Exception) {
            Log.w(tag, "TCP send failed: ${e.message}")
        }
    }

    private fun startTcpReadLoop() {
        readJob = clientScope.launch {
            val stream = dataIn ?: return@launch
            try {
                while (isActive) {
                    val length = stream.readInt()
                    if (length <= 0 || length > 65536) break

                    val buffer = ByteArray(length)
                    stream.readFully(buffer)
                    val jsonStr = String(buffer, Charsets.UTF_8)
                    val obj = JSONObject(jsonStr)

                    handleServerMessage(obj)
                }
            } catch (e: Exception) {
                Log.i(tag, "TCP read stream ended: ${e.message}")
            } finally {
                disconnect()
            }
        }
    }

    private fun handleServerMessage(obj: JSONObject) {
        when (obj.optString("type")) {
            "hello_reply" -> {
                val needsPairing = obj.optBoolean("needs_pairing", true)
                if (needsPairing && !_connectionState.value.isConnected) {
                    _connectionState.value = _connectionState.value.copy(
                        isConnecting = false,
                        needsPairingPin = true
                    )
                }
            }
            "pair_reply" -> {
                val status = obj.optString("status")
                if (status == "success") {
                    val token = obj.optString("token")
                    val host = _connectionState.value.serverIp
                    prefs.edit().putString("auth_token_$host", token).apply()

                    _connectionState.value = _connectionState.value.copy(
                        isConnected = true,
                        isConnecting = false,
                        needsPairingPin = false,
                        errorMessage = null
                    )
                } else {
                    _connectionState.value = _connectionState.value.copy(
                        errorMessage = obj.optString("message", "Pairing rejected.")
                    )
                }
            }
            "auth_reply" -> {
                val status = obj.optString("status")
                if (status == "success") {
                    _connectionState.value = _connectionState.value.copy(
                        isConnected = true,
                        isConnecting = false,
                        needsPairingPin = false,
                        errorMessage = null
                    )
                } else {
                    _connectionState.value = _connectionState.value.copy(
                        isConnecting = false,
                        needsPairingPin = true
                    )
                }
            }
            "pong" -> {
                val now = System.currentTimeMillis()
                lastRttMs = (now - lastPingSentMs).toFloat()
                _connectionState.value = _connectionState.value.copy(
                    latencyMs = lastRttMs
                )
            }
        }
    }

    private fun startPingLoop() {
        pingJob = clientScope.launch {
            while (isActive) {
                lastPingSentMs = System.currentTimeMillis()
                sendTcpMessage(ProtocolPackets.createPing(lastPingSentMs, lastRttMs))
                delay(1000)
            }
        }
    }
}
