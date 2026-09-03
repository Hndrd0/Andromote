package com.wiimote.andromote

import android.content.pm.ActivityInfo
import android.os.Bundle
import android.view.KeyEvent
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.lifecycleScope
import com.wiimote.andromote.model.DiscoveredServer
import com.wiimote.andromote.model.MotionTelemetry
import com.wiimote.andromote.network.DiscoveryClient
import com.wiimote.andromote.network.NetworkClient
import com.wiimote.andromote.sensors.MotionSensorManager
import com.wiimote.andromote.ui.screens.CalibrationScreen
import com.wiimote.andromote.ui.screens.ConnectionScreen
import com.wiimote.andromote.ui.screens.ControllerScreen
import com.wiimote.andromote.ui.theme.AndromoteTheme
import kotlinx.coroutines.launch

enum class AppScreen {
    CONTROLLER,
    CONNECTION,
    CALIBRATION
}

class MainActivity : ComponentActivity() {

    private lateinit var networkClient: NetworkClient
    private lateinit var discoveryClient: DiscoveryClient
    private lateinit var motionSensorManager: MotionSensorManager

    private var currentTelemetry by mutableStateOf(MotionTelemetry())
    private var currentScreen by mutableStateOf(AppScreen.CONTROLLER)
    private var discoveredServers by mutableStateOf<List<DiscoveredServer>>(emptyList())
    private var isScanning by mutableStateOf(false)
    private var isMotionActive by mutableStateOf(true)
    private var isPhysicalLandscape by mutableStateOf(false)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Force full sensor orientation regardless of system rotation lock
        try {
            requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_FULL_SENSOR
        } catch (e: Exception) {}

        // Keep screen awake while controller is open
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        networkClient = NetworkClient(this)
        discoveryClient = DiscoveryClient()

        motionSensorManager = MotionSensorManager(
            context = this,
            onSensorFrame = { qx, qy, qz, qw, gx, gy, gz, ax, ay, az, ts ->
                networkClient.sendMotion(qx, qy, qz, qw, gx, gy, gz, ax, ay, az, ts)
            },
            onTelemetryUpdate = { telem ->
                currentTelemetry = telem
            }
        )
        motionSensorManager.onOrientationChanged = { isLandscape ->
            runOnUiThread {
                isPhysicalLandscape = isLandscape
            }
        }

        // Trigger initial discovery scan
        startScan()

        setContent {
            AndromoteTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val connState by networkClient.connectionState.collectAsState()

                    // Start or stop sensors based on connection state
                    LaunchedEffect(connState.isConnected) {
                        if (connState.isConnected) {
                            motionSensorManager.isMotionActive = isMotionActive
                            motionSensorManager.start()
                        } else {
                            motionSensorManager.stop()
                        }
                    }

                    when (currentScreen) {
                        AppScreen.CONTROLLER -> {
                            ControllerScreen(
                                connectionState = connState,
                                isLandscape = isPhysicalLandscape,
                                isMotionActive = isMotionActive,
                                onToggleMotion = {
                                    isMotionActive = !isMotionActive
                                    motionSensorManager.isMotionActive = isMotionActive
                                },
                                onButtonEvent = { btn, state ->
                                    networkClient.sendButton(btn, state)
                                },
                                onRecenter = {
                                    networkClient.sendRecenter()
                                },
                                onNavigateToConnection = {
                                    startScan()
                                    currentScreen = AppScreen.CONNECTION
                                },
                                onNavigateToCalibration = {
                                    currentScreen = AppScreen.CALIBRATION
                                }
                            )
                        }
                        AppScreen.CONNECTION -> {
                            ConnectionScreen(
                                connectionState = connState,
                                discoveredServers = discoveredServers,
                                isScanning = isScanning,
                                onScan = { startScan() },
                                onConnectServer = { ip, tcpPort, motionPort ->
                                    networkClient.connect(ip, tcpPort, motionPort)
                                },
                                onSubmitPin = { pin ->
                                    networkClient.submitPin(pin)
                                },
                                onDisconnect = {
                                    networkClient.disconnect()
                                }
                            )
                        }
                        AppScreen.CALIBRATION -> {
                            CalibrationScreen(
                                telemetry = currentTelemetry,
                                onRecenter = { networkClient.sendRecenter() }
                            )
                        }
                    }
                }
            }
        }
    }

    private fun startScan() {
        if (isScanning) return
        isScanning = true
        lifecycleScope.launch {
            discoveredServers = discoveryClient.scanForServers(timeoutMs = 2500)
            isScanning = false
        }
    }

    override fun onResume() {
        super.onResume()
        val connState = networkClient.connectionState.value
        if (connState.isConnected) {
            motionSensorManager.start()
        }
    }

    override fun onPause() {
        super.onPause()
        // Save battery by turning off sensors in background
        motionSensorManager.stop()
    }

    override fun onDestroy() {
        super.onDestroy()
        motionSensorManager.stop()
        networkClient.disconnect()
    }

    // Physical Volume Rocker mapped as ergonomic B Trigger
    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_VOLUME_DOWN || keyCode == KeyEvent.KEYCODE_VOLUME_UP) {
            networkClient.sendButton("B", "down")
            return true
        }
        return super.onKeyDown(keyCode, event)
    }

    override fun onKeyUp(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_VOLUME_DOWN || keyCode == KeyEvent.KEYCODE_VOLUME_UP) {
            networkClient.sendButton("B", "up")
            return true
        }
        return super.onKeyUp(keyCode, event)
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (currentScreen != AppScreen.CONTROLLER) {
            currentScreen = AppScreen.CONTROLLER
        } else {
            super.onBackPressed()
        }
    }
}
