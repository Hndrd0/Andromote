package com.wiimote.andromote.network

import android.util.Log
import com.wiimote.andromote.model.DiscoveredServer
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.SocketTimeoutException

class DiscoveryClient(private val discoveryPort: Int = 42424) {

    private val tag = "DiscoveryClient"

    suspend fun scanForServers(timeoutMs: Long = 2000): List<DiscoveredServer> = withContext(Dispatchers.IO) {
        val servers = mutableMapOf<String, DiscoveredServer>()
        var socket: DatagramSocket? = null

        try {
            socket = DatagramSocket()
            socket.broadcast = true
            socket.soTimeout = 300 // short timeout per packet read

            val requestJson = JSONObject().apply {
                put("type", "discovery_request")
            }.toString().toByteArray(Charsets.UTF_8)

            // Broadcast to LAN
            val broadcastAddr = InetAddress.getByName("255.255.255.255")
            val sendPacket = DatagramPacket(requestJson, requestJson.size, broadcastAddr, discoveryPort)
            socket.send(sendPacket)

            val buffer = ByteArray(2048)
            val startTime = System.currentTimeMillis()

            while (System.currentTimeMillis() - startTime < timeoutMs) {
                try {
                    val recvPacket = DatagramPacket(buffer, buffer.size)
                    socket.receive(recvPacket)

                    val jsonStr = String(recvPacket.data, 0, recvPacket.length, Charsets.UTF_8)
                    val obj = JSONObject(jsonStr)

                    if (obj.optString("type") == "discovery_response") {
                        val senderIp = recvPacket.address.hostAddress ?: obj.optString("ip", "127.0.0.1")
                        val hostname = obj.optString("hostname", "PC")
                        val tcpPort = obj.optInt("tcp_port", 42425)
                        val motionPort = obj.optInt("motion_port", 42426)
                        val dsuPort = obj.optInt("dsu_port", 26760)

                        val server = DiscoveredServer(
                            hostname = hostname,
                            ip = senderIp,
                            tcpPort = tcpPort,
                            motionPort = motionPort,
                            dsuPort = dsuPort
                        )
                        servers[senderIp] = server
                        Log.d(tag, "Discovered receiver at $senderIp ($hostname)")
                    }
                } catch (e: SocketTimeoutException) {
                    // Loop continues until timeoutMs expires
                } catch (e: Exception) {
                    Log.w(tag, "Error parsing discovery packet: ${e.message}")
                }
            }
        } catch (e: Exception) {
            Log.e(tag, "Discovery broadcast failed: ${e.message}")
        } finally {
            try {
                socket?.close()
            } catch (e: Exception) {}
        }

        servers.values.toList()
    }
}
