package com.wiimote.andromote.model

data class DiscoveredServer(
    val hostname: String,
    val ip: String,
    val tcpPort: Int,
    val motionPort: Int,
    val dsuPort: Int
)

data class MotionTelemetry(
    val yawDeg: Float = 0f,
    val pitchDeg: Float = 0f,
    val rollDeg: Float = 0f,
    val gyroX: Float = 0f,
    val gyroY: Float = 0f,
    val gyroZ: Float = 0f,
    val accelX: Float = 0f,
    val accelY: Float = 0f,
    val accelZ: Float = 9.81f,
    val packetCount: Long = 0L,
    val packetRateHz: Float = 0f
)

data class ConnectionState(
    val isConnected: Boolean = false,
    val isConnecting: Boolean = false,
    val serverName: String = "",
    val serverIp: String = "",
    val latencyMs: Float = 0f,
    val errorMessage: String? = null,
    val needsPairingPin: Boolean = false
)
