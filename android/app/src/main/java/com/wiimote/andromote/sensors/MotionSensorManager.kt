package com.wiimote.andromote.sensors

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Handler
import android.os.HandlerThread
import android.os.Process
import com.wiimote.andromote.model.MotionTelemetry
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.math.atan2
import kotlin.math.asin

class MotionSensorManager(
    context: Context,
    private val onSensorFrame: (qx: Float, qy: Float, qz: Float, qw: Float,
                                gx: Float, gy: Float, gz: Float,
                                ax: Float, ay: Float, az: Float,
                                timestampMs: Long) -> Unit,
    private val onTelemetryUpdate: (MotionTelemetry) -> Unit
) : SensorEventListener {

    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager

    private var rotationSensor: Sensor? = null
    private var gyroSensor: Sensor? = null
    private var accelSensor: Sensor? = null

    private val isRunning = AtomicBoolean(false)
    @Volatile var isMotionActive: Boolean = true
    var onOrientationChanged: ((isLandscape: Boolean) -> Unit)? = null

    @Volatile private var isCurrentlyLandscape: Boolean = false
    private var gravityAxEma = 0f
    private var gravityAyEma = 9.81f

    private var sensorThread: HandlerThread? = null
    private var sensorHandler: Handler? = null

    // Current sensor values
    @Volatile private var curQx = 0f
    @Volatile private var curQy = 0f
    @Volatile private var curQz = 0f
    @Volatile private var curQw = 1f

    @Volatile private var curGx = 0f
    @Volatile private var curGy = 0f
    @Volatile private var curGz = 0f

    @Volatile private var curAx = 0f
    @Volatile private var curAy = 0f
    @Volatile private var curAz = 9.81f

    private var packetCount = 0L
    private var lastTelemetryUpdate = 0L

    init {
        // Prefer GAME_ROTATION_VECTOR (no magnetic drift), fallback to standard ROTATION_VECTOR
        rotationSensor = sensorManager.getDefaultSensor(Sensor.TYPE_GAME_ROTATION_VECTOR)
            ?: sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)

        gyroSensor = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE)
        accelSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
    }

    val isSupported: Boolean
        get() = (rotationSensor != null || gyroSensor != null) && accelSensor != null

    fun start() {
        if (isRunning.compareAndSet(false, true)) {
            val thread = HandlerThread("MotionSensorThread", Process.THREAD_PRIORITY_MORE_FAVORABLE)
            thread.start()
            sensorThread = thread
            val handler = Handler(thread.looper)
            sensorHandler = handler

            rotationSensor?.let {
                sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_FASTEST, handler)
            }
            gyroSensor?.let {
                sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_FASTEST, handler)
            }
            accelSensor?.let {
                sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_FASTEST, handler)
            }
        }
    }

    fun stop() {
        if (isRunning.compareAndSet(true, false)) {
            sensorManager.unregisterListener(this)
            sensorThread?.quitSafely()
            sensorThread = null
            sensorHandler = null
        }
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (event == null || !isRunning.get()) return

        when (event.sensor.type) {
            Sensor.TYPE_GAME_ROTATION_VECTOR, Sensor.TYPE_ROTATION_VECTOR -> {
                val q = FloatArray(4)
                SensorManager.getQuaternionFromVector(q, event.values)
                curQw = q[0]
                curQx = q[1]
                curQy = q[2]
                curQz = q[3]

                // If device lacks a physical gyroscope, rotation vector drives frame emission
                if (gyroSensor == null) {
                    emitFrame()
                }
            }
            Sensor.TYPE_GYROSCOPE -> {
                curGx = event.values[0]
                curGy = event.values[1]
                curGz = event.values[2]

                // Gyroscope is the primary sensor for low-latency air-mouse angular velocity
                emitFrame()
            }
            Sensor.TYPE_ACCELEROMETER -> {
                curAx = event.values[0]
                curAy = event.values[1]
                curAz = event.values[2]

                // Low-pass filter gravity for physical orientation detection
                gravityAxEma = 0.15f * curAx + 0.85f * gravityAxEma
                gravityAyEma = 0.15f * curAy + 0.85f * gravityAyEma

                val absAx = Math.abs(gravityAxEma)
                val absAy = Math.abs(gravityAyEma)

                // Hysteresis: flip to landscape if horizontal gravity exceeds vertical by 1.5 m/s^2
                val newIsLandscape = if (isCurrentlyLandscape) {
                    absAx > (absAy - 1.5f) && absAx > 4.5f
                } else {
                    absAx > (absAy + 1.5f) && absAx > 5.5f
                }

                if (newIsLandscape != isCurrentlyLandscape) {
                    isCurrentlyLandscape = newIsLandscape
                    onOrientationChanged?.invoke(newIsLandscape)
                }

                // If neither gyro nor rotation vector sensor exists
                if (gyroSensor == null && rotationSensor == null) {
                    emitFrame()
                }
            }
        }
    }

    private fun emitFrame() {
        packetCount++
        val now = System.currentTimeMillis()

        // Stream high-rate frame to network when motion is active
        if (isMotionActive) {
            onSensorFrame(curQx, curQy, curQz, curQw, curGx, curGy, curGz, curAx, curAy, curAz, now)
        }

        // Throttle UI telemetry updates to ~20 Hz (every 50ms) to conserve CPU & battery
        if (now - lastTelemetryUpdate >= 50) {
            lastTelemetryUpdate = now

            // Convert quaternion to Euler angles in degrees
            val sinp = 2.0f * (curQw * curQx - curQy * curQz)
            val pitch = Math.toDegrees(if (Math.abs(sinp) >= 1.0f) Math.copySign(Math.PI / 2.0, sinp.toDouble()) else asin(sinp.toDouble())).toFloat()

            val sinyCosp = 2.0f * (curQw * curQz + curQx * curQy)
            val cosyCosp = 1.0f - 2.0f * (curQx * curQx + curQz * curQz)
            val yaw = Math.toDegrees(atan2(sinyCosp.toDouble(), cosyCosp.toDouble())).toFloat()

            val sinrCosp = 2.0f * (curQw * curQy + curQz * curQx)
            val cosrCosp = 1.0f - 2.0f * (curQx * curQx + curQy * curQy)
            val roll = Math.toDegrees(atan2(sinrCosp.toDouble(), cosrCosp.toDouble())).toFloat()

            onTelemetryUpdate(
                MotionTelemetry(
                    yawDeg = yaw,
                    pitchDeg = pitch,
                    rollDeg = roll,
                    gyroX = curGx,
                    gyroY = curGy,
                    gyroZ = curGz,
                    accelX = curAx,
                    accelY = curAy,
                    accelZ = curAz,
                    packetCount = packetCount
                )
            )
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
}
