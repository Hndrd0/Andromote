package com.wiimote.andromote.network

import org.json.JSONObject
import java.nio.ByteBuffer
import java.nio.ByteOrder

object ProtocolPackets {

    const val BINARY_MAGIC = "WMO1"
    const val BINARY_PACKET_SIZE = 54

    /**
     * Packs sensor readings into a compact 54-byte big-endian binary struct:
     * 4s (Magic) + H (Seq) + Q (Timestamp) + 4f (Quat) + 3f (Gyro) + 3f (Accel)
     */
    fun packBinaryMotion(
        seq: Short,
        timestampMs: Long,
        qx: Float, qy: Float, qz: Float, qw: Float,
        gx: Float, gy: Float, gz: Float,
        ax: Float, ay: Float, az: Float
    ): ByteArray {
        val buffer = ByteBuffer.allocate(BINARY_PACKET_SIZE).order(ByteOrder.BIG_ENDIAN)
        buffer.put(BINARY_MAGIC.toByteArray(Charsets.US_ASCII))
        buffer.putShort(seq)
        buffer.putLong(timestampMs)
        buffer.putFloat(qx)
        buffer.putFloat(qy)
        buffer.putFloat(qz)
        buffer.putFloat(qw)
        buffer.putFloat(gx)
        buffer.putFloat(gy)
        buffer.putFloat(gz)
        buffer.putFloat(ax)
        buffer.putFloat(ay)
        buffer.putFloat(az)
        return buffer.array()
    }

    fun createHello(deviceId: String): String {
        return JSONObject().apply {
            put("type", "hello")
            put("device_id", deviceId)
            put("protocol_version", 1)
        }.toString()
    }

    fun createPair(pin: String, deviceId: String, deviceName: String): String {
        return JSONObject().apply {
            put("type", "pair")
            put("pin", pin)
            put("device_id", deviceId)
            put("device_name", deviceName)
        }.toString()
    }

    fun createAuth(token: String, deviceId: String, deviceName: String): String {
        return JSONObject().apply {
            put("type", "auth")
            put("token", token)
            put("device_id", deviceId)
            put("device_name", deviceName)
        }.toString()
    }

    fun createButton(button: String, state: String, timestampMs: Long): String {
        return JSONObject().apply {
            put("type", "button")
            put("button", button)
            put("state", state)
            put("timestamp", timestampMs)
        }.toString()
    }

    fun createRecenter(): String {
        return JSONObject().apply {
            put("type", "recenter")
        }.toString()
    }

    fun createPing(timestampMs: Long, lastRttMs: Float): String {
        return JSONObject().apply {
            put("type", "ping")
            put("timestamp", timestampMs)
            put("last_rtt", lastRttMs)
        }.toString()
    }

    fun createTouchpadMove(dx: Float, dy: Float): String {
        return JSONObject().apply {
            put("type", "touchpad_move")
            put("dx", dx.toDouble())
            put("dy", dy.toDouble())
        }.toString()
    }

    fun createTouchpadTap(fingers: Int): String {
        return JSONObject().apply {
            put("type", "touchpad_tap")
            put("fingers", fingers)
        }.toString()
    }
}
