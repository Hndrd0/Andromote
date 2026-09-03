package com.wiimote.andromote.ui.components

import android.view.HapticFeedbackConstants
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.wiimote.andromote.ui.theme.*

/**
 * Authentic Ergonomic Touch-Mouse:
 * Blends the physical anatomy of an ergonomic mouse with a high-precision touchpad surface:
 * - Mouse Top Lobes: Left Click, Tactile Center Scroll Wheel (with Wheel Click), and Right Click
 * - Center Palm Rest: Integrated Precision Touchpad for silky sub-pixel cursor glide & tap-to-click
 * - Thumb Wing: Mouse 4 (Back) & Mouse 5 (Forward)
 * - Base Deck: Left-Click Drag Lock, Hardware DPI Switch (800 / 1600 / 2400 DPI), Lift Clutch, and Recenter
 */
@Composable
fun AirMousePad(
    isMotionFrozen: Boolean,
    onToggleFreeze: () -> Unit,
    onButtonEvent: (button: String, state: String) -> Unit,
    onRecenter: () -> Unit,
    onTouchMove: ((dx: Float, dy: Float) -> Unit)? = null
) {
    var isDragLocked by remember { mutableStateOf(false) }
    var currentDpiIndex by remember { mutableStateOf(1) } // 0: 800, 1: 1600, 2: 2400
    val dpiLevels = listOf("800 DPI", "1600 DPI", "2400 DPI")
    var touchCursorPos by remember { mutableStateOf<Offset?>(null) }
    val view = LocalView.current

    // Mouse Chassis Container (Shaped like a sleek modern computer mouse)
    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 8.dp, vertical = 4.dp)
            .clip(RoundedCornerShape(topStart = 32.dp, topEnd = 32.dp, bottomStart = 24.dp, bottomEnd = 24.dp))
            .background(BgPrimary)
            .border(
                width = 1.5.dp,
                color = BorderSubtle,
                shape = RoundedCornerShape(topStart = 32.dp, topEnd = 32.dp, bottomStart = 24.dp, bottomEnd = 24.dp)
            )
            .padding(10.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // --- 1. Top Mouse Lobes: Left Click | Central Wheel | Right Click ---
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(95.dp),
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                // Left Click (Primary Mouse Button)
                AirMouseButton(
                    label = "LEFT CLICK",
                    sublabel = if (isDragLocked) "LOCKED (HOLD)" else "Primary Click",
                    modifier = Modifier
                        .weight(1.2f)
                        .fillMaxHeight(),
                    accentColor = if (isDragLocked) AccentAmber else AccentCyan,
                    textColor = BgPrimary,
                    fontSize = 13.sp,
                    onButtonEvent = { state ->
                        if (!isDragLocked) {
                            onButtonEvent("MOUSE_LEFT", state)
                        }
                    }
                )

                // Central Mechanical Scroll Wheel & Middle Click
                IntegratedScrollWheel(
                    modifier = Modifier
                        .weight(0.9f)
                        .fillMaxHeight(),
                    onScroll = { isUp ->
                        val btn = if (isUp) "MOUSE_WHEEL_UP" else "MOUSE_WHEEL_DOWN"
                        onButtonEvent(btn, "down")
                        onButtonEvent(btn, "up")
                    },
                    onMiddleClick = { state ->
                        onButtonEvent("MOUSE_MIDDLE", state)
                    }
                )

                // Right Click (Secondary Mouse Button)
                AirMouseButton(
                    label = "RIGHT CLICK",
                    sublabel = "Context Menu",
                    modifier = Modifier
                        .weight(1.1f)
                        .fillMaxHeight(),
                    accentColor = BgElevated,
                    textColor = TextPrimary,
                    borderColor = BorderSubtle,
                    fontSize = 13.sp,
                    onButtonEvent = { state -> onButtonEvent("MOUSE_RIGHT", state) }
                )
            }

            Spacer(modifier = Modifier.height(6.dp))

            // --- 2. Central Palm Rest: Precision Touchpad Surface ---
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .clip(RoundedCornerShape(16.dp))
                    .background(BgSurface)
                    .border(1.dp, BorderSubtle, RoundedCornerShape(16.dp))
                    .pointerInput(Unit) {
                        detectTapGestures(
                            onTap = {
                                view.performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY)
                                onButtonEvent("MOUSE_LEFT", "down")
                                onButtonEvent("MOUSE_LEFT", "up")
                            },
                            onLongPress = {
                                view.performHapticFeedback(HapticFeedbackConstants.LONG_PRESS)
                                onButtonEvent("MOUSE_RIGHT", "down")
                                onButtonEvent("MOUSE_RIGHT", "up")
                            }
                        )
                    }
                    .pointerInput(Unit) {
                        detectDragGestures(
                            onDragStart = { offset ->
                                touchCursorPos = offset
                            },
                            onDragEnd = {
                                touchCursorPos = null
                            },
                            onDragCancel = {
                                touchCursorPos = null
                            },
                            onDrag = { change, dragAmount ->
                                change.consume()
                                touchCursorPos = change.position
                                val scale = when (currentDpiIndex) {
                                    0 -> 0.8f
                                    1 -> 1.4f
                                    else -> 2.2f
                                }
                                if (!isMotionFrozen) {
                                    onTouchMove?.invoke(dragAmount.x * scale, dragAmount.y * scale)
                                }
                            }
                        )
                    },
                contentAlignment = Alignment.Center
            ) {
                // Subtle Touchpad Guide Crosshair & Watermark
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Text("✦", color = AccentCyan.copy(alpha = 0.6f), fontSize = 16.sp)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "PRECISION TOUCHPAD",
                        color = TextSecondary.copy(alpha = 0.8f),
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = "Glide to move cursor • Tap to click",
                        color = TextTertiary,
                        fontSize = 9.sp
                    )
                }

                // Visual Touch Cursor Indicator
                touchCursorPos?.let { pos ->
                    Box(
                        modifier = Modifier
                            .offset(x = (pos.x.toInt() - 14).dp, y = (pos.y.toInt() - 14).dp)
                            .size(28.dp)
                            .clip(RoundedCornerShape(14.dp))
                            .background(AccentCyan.copy(alpha = 0.3f))
                            .border(1.5.dp, AccentCyan, RoundedCornerShape(14.dp))
                    )
                }
            }

            Spacer(modifier = Modifier.height(6.dp))

            // --- 3. Thumb Wing: Mouse 4 & Mouse 5 ---
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(44.dp),
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                AirMouseButton(
                    label = "◀ BACK (M4)",
                    sublabel = "Navigate",
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight(),
                    accentColor = BgElevated,
                    textColor = TextPrimary,
                    borderColor = BorderSubtle,
                    fontSize = 11.sp,
                    onButtonEvent = { state -> onButtonEvent("MOUSE_BACK", state) }
                )

                AirMouseButton(
                    label = "FORWARD (M5) ▶",
                    sublabel = "Navigate",
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight(),
                    accentColor = BgElevated,
                    textColor = TextPrimary,
                    borderColor = BorderSubtle,
                    fontSize = 11.sp,
                    onButtonEvent = { state -> onButtonEvent("MOUSE_FORWARD", state) }
                )
            }

            Spacer(modifier = Modifier.height(6.dp))

            // --- 4. Mouse Base Deck: Double Click, Drag Lock, DPI, Lift Clutch, Recenter ---
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(42.dp),
                horizontalArrangement = Arrangement.spacedBy(5.dp)
            ) {
                // 2x Click
                AirMouseQuickButton(
                    label = "2x Click",
                    modifier = Modifier
                        .weight(0.9f)
                        .fillMaxHeight(),
                    accentColor = BgElevated,
                    textColor = TextPrimary,
                    fontSize = 10.sp,
                    onClick = {
                        onButtonEvent("MOUSE_LEFT", "down")
                        onButtonEvent("MOUSE_LEFT", "up")
                        onButtonEvent("MOUSE_LEFT", "down")
                        onButtonEvent("MOUSE_LEFT", "up")
                    }
                )

                // Drag Lock Toggle
                Button(
                    onClick = {
                        view.performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY)
                        isDragLocked = !isDragLocked
                        if (isDragLocked) {
                            onButtonEvent("MOUSE_LEFT", "down")
                        } else {
                            onButtonEvent("MOUSE_LEFT", "up")
                        }
                    },
                    modifier = Modifier
                        .weight(1.05f)
                        .fillMaxHeight(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isDragLocked) AccentAmber else BgElevated,
                        contentColor = if (isDragLocked) BgPrimary else TextPrimary
                    ),
                    shape = RoundedCornerShape(8.dp),
                    border = if (!isDragLocked) androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle) else null,
                    contentPadding = PaddingValues(horizontal = 2.dp, vertical = 2.dp)
                ) {
                    Text(
                        text = if (isDragLocked) "Locked" else "Drag Lock",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                // DPI Switch
                Button(
                    onClick = {
                        view.performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK)
                        currentDpiIndex = (currentDpiIndex + 1) % dpiLevels.size
                    },
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = BgElevated,
                        contentColor = AccentCyan
                    ),
                    shape = RoundedCornerShape(8.dp),
                    border = androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle),
                    contentPadding = PaddingValues(horizontal = 2.dp, vertical = 2.dp)
                ) {
                    Text(
                        text = dpiLevels[currentDpiIndex],
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = AccentCyan
                    )
                }

                // Lift Clutch (Pointer Freeze)
                Button(
                    onClick = onToggleFreeze,
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isMotionFrozen) AccentAmber else BgElevated,
                        contentColor = if (isMotionFrozen) BgPrimary else TextPrimary
                    ),
                    shape = RoundedCornerShape(8.dp),
                    border = if (!isMotionFrozen) androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle) else null,
                    contentPadding = PaddingValues(horizontal = 2.dp, vertical = 2.dp)
                ) {
                    Text(
                        text = if (isMotionFrozen) "Paused" else "Clutch",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                // Recenter
                Button(
                    onClick = onRecenter,
                    modifier = Modifier
                        .weight(0.9f)
                        .fillMaxHeight(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = AccentGreen,
                        contentColor = BgPrimary
                    ),
                    shape = RoundedCornerShape(8.dp),
                    contentPadding = PaddingValues(horizontal = 2.dp, vertical = 2.dp)
                ) {
                    Text("Center", fontSize = 10.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

/**
 * Tactile Mouse Button with press/release dispatch and haptics.
 */
@Composable
fun AirMouseButton(
    label: String,
    sublabel: String? = null,
    modifier: Modifier = Modifier,
    accentColor: Color = BgElevated,
    textColor: Color = TextPrimary,
    borderColor: Color? = null,
    fontSize: androidx.compose.ui.unit.TextUnit = 13.sp,
    onButtonEvent: (state: String) -> Unit
) {
    val view = LocalView.current
    var isPressed by remember { mutableStateOf(false) }

    val curBg = if (isPressed) AccentCyan else accentColor
    val curTextColor = if (isPressed) BgPrimary else textColor

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .background(curBg)
            .then(
                if (borderColor != null && !isPressed) Modifier.border(1.dp, borderColor, RoundedCornerShape(12.dp))
                else Modifier
            )
            .pointerInput(Unit) {
                detectTapGestures(
                    onPress = {
                        isPressed = true
                        view.performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY)
                        onButtonEvent("down")
                        val released = tryAwaitRelease()
                        isPressed = false
                        if (released) {
                            view.performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY_RELEASE)
                        }
                        onButtonEvent("up")
                    }
                )
            },
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(horizontal = 4.dp)
        ) {
            Text(
                text = label,
                color = curTextColor,
                fontSize = fontSize,
                fontWeight = FontWeight.Bold
            )
            if (sublabel != null) {
                Spacer(modifier = Modifier.height(1.dp))
                Text(
                    text = sublabel,
                    color = curTextColor.copy(alpha = 0.7f),
                    fontSize = 9.sp
                )
            }
        }
    }
}

/**
 * Integrated Vertical Scroll Wheel Strip with ribbed physical styling,
 * drag-to-scroll, and tap-to-Middle-Click.
 */
@Composable
fun IntegratedScrollWheel(
    modifier: Modifier = Modifier,
    onScroll: (isUp: Boolean) -> Unit,
    onMiddleClick: (state: String) -> Unit
) {
    val view = LocalView.current
    var isWheelPressed by remember { mutableStateOf(false) }
    var accumulatedDrag by remember { mutableStateOf(0f) }
    val dragThreshold = 20f

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .background(if (isWheelPressed) AccentCyan.copy(alpha = 0.25f) else BgElevated)
            .border(1.dp, if (isWheelPressed) AccentCyan else BorderSubtle, RoundedCornerShape(12.dp))
            .pointerInput(Unit) {
                detectTapGestures(
                    onPress = {
                        isWheelPressed = true
                        view.performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY)
                        onMiddleClick("down")
                        val released = tryAwaitRelease()
                        isWheelPressed = false
                        if (released) {
                            view.performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY_RELEASE)
                        }
                        onMiddleClick("up")
                    }
                )
            }
            .pointerInput(Unit) {
                detectDragGestures { change, dragAmount ->
                    change.consume()
                    accumulatedDrag += dragAmount.y
                    if (accumulatedDrag <= -dragThreshold) {
                        view.performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK)
                        onScroll(true)
                        accumulatedDrag = 0f
                    } else if (accumulatedDrag >= dragThreshold) {
                        view.performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK)
                        onScroll(false)
                        accumulatedDrag = 0f
                    }
                }
            },
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.padding(vertical = 6.dp)
        ) {
            Text("▲", color = AccentCyan, fontSize = 11.sp)
            Spacer(modifier = Modifier.height(3.dp))

            // Simulated Wheel Tread
            Column(
                modifier = Modifier
                    .width(26.dp)
                    .height(30.dp)
                    .clip(RoundedCornerShape(5.dp))
                    .background(Color(0xFF0E0E16))
                    .border(1.dp, BorderSubtle, RoundedCornerShape(5.dp))
                    .padding(vertical = 3.dp),
                verticalArrangement = Arrangement.SpaceEvenly,
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                repeat(4) {
                    Box(
                        modifier = Modifier
                            .width(16.dp)
                            .height(2.dp)
                            .background(if (isWheelPressed) AccentCyan else TextSecondary.copy(alpha = 0.4f))
                    )
                }
            }

            Spacer(modifier = Modifier.height(3.dp))
            Text("WHEEL", color = TextSecondary, fontSize = 8.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(1.dp))
            Text("▼", color = AccentCyan, fontSize = 11.sp)
        }
    }
}

/**
 * Quick tap button with haptic feedback.
 */
@Composable
fun AirMouseQuickButton(
    label: String,
    modifier: Modifier = Modifier,
    accentColor: Color = BgElevated,
    textColor: Color = TextPrimary,
    fontSize: androidx.compose.ui.unit.TextUnit = 11.sp,
    onClick: () -> Unit
) {
    val view = LocalView.current
    Button(
        onClick = {
            view.performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY)
            onClick()
        },
        modifier = modifier,
        colors = ButtonDefaults.buttonColors(
            containerColor = accentColor,
            contentColor = textColor
        ),
        shape = RoundedCornerShape(8.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle),
        contentPadding = PaddingValues(horizontal = 4.dp, vertical = 2.dp)
    ) {
        Text(text = label, fontSize = fontSize, fontWeight = FontWeight.SemiBold)
    }
}
