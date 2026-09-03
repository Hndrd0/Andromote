package com.wiimote.andromote.ui.components

import android.view.HapticFeedbackConstants
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.wiimote.andromote.ui.theme.*

/**
 * Authentic Air Mouse Pad:
 * Turns the phone into a true, ergonomic desktop computer mouse with:
 * - Primary Left Click, Central Scroll Wheel (with Middle Click), and Right Click
 * - Side Thumb Buttons: Mouse 4 (Back) and Mouse 5 (Forward)
 * - Quick Double Click and Left-Click Drag Lock
 * - Hardware DPI Selector (800 / 1600 / 2400 DPI)
 * - Lift Clutch (Cursor Freeze) and Zero-Angle Recenter
 */
@Composable
fun AirMousePad(
    isMotionFrozen: Boolean,
    onToggleFreeze: () -> Unit,
    onButtonEvent: (button: String, state: String) -> Unit,
    onRecenter: () -> Unit
) {
    var isDragLocked by remember { mutableStateOf(false) }
    var currentDpiIndex by remember { mutableStateOf(1) } // 0: 800, 1: 1600, 2: 2400
    val dpiLevels = listOf("800 DPI", "1600 DPI", "2400 DPI")
    val view = LocalView.current

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 14.dp, vertical = 10.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        // --- 1. Ergonomic Mouse Top Shell: Left Click | Scroll Wheel / Middle Click | Right Click ---
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1.35f),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Left Click (Primary Button)
            AirMouseButton(
                label = "LEFT CLICK",
                sublabel = if (isDragLocked) "DRAG LOCKED" else "Primary / Select",
                modifier = Modifier
                    .weight(1.25f)
                    .fillMaxHeight(),
                accentColor = if (isDragLocked) AccentAmber else AccentCyan,
                textColor = BgPrimary,
                fontSize = 15.sp,
                onButtonEvent = { state ->
                    if (!isDragLocked) {
                        onButtonEvent("MOUSE_LEFT", state)
                    }
                }
            )

            // Center Column: Tactile Scroll Wheel & Middle Click
            IntegratedScrollWheel(
                modifier = Modifier
                    .weight(0.95f)
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

            // Right Click (Secondary Button)
            AirMouseButton(
                label = "RIGHT CLICK",
                sublabel = "Context Menu",
                modifier = Modifier
                    .weight(1.1f)
                    .fillMaxHeight(),
                accentColor = BgElevated,
                textColor = TextPrimary,
                borderColor = BorderSubtle,
                fontSize = 14.sp,
                onButtonEvent = { state -> onButtonEvent("MOUSE_RIGHT", state) }
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        // --- 2. Side / Thumb Navigation Buttons (Mouse 4 & Mouse 5) ---
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(54.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Mouse 4 (Browser Back)
            AirMouseButton(
                label = "◀ BACK (MOUSE 4)",
                sublabel = "Browser / File Nav",
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight(),
                accentColor = BgElevated,
                textColor = TextPrimary,
                borderColor = BorderSubtle,
                fontSize = 12.sp,
                onButtonEvent = { state -> onButtonEvent("MOUSE_BACK", state) }
            )

            // Mouse 5 (Browser Forward)
            AirMouseButton(
                label = "FORWARD (MOUSE 5) ▶",
                sublabel = "Browser / File Nav",
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight(),
                accentColor = BgElevated,
                textColor = TextPrimary,
                borderColor = BorderSubtle,
                fontSize = 12.sp,
                onButtonEvent = { state -> onButtonEvent("MOUSE_FORWARD", state) }
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        // --- 3. Productivity Mouse Tools: Double Click, Drag Lock, DPI Switch ---
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Instant Double Click
            AirMouseQuickButton(
                label = "Double Click",
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight(),
                accentColor = BgElevated,
                textColor = TextPrimary,
                fontSize = 11.sp,
                onClick = {
                    onButtonEvent("MOUSE_LEFT", "down")
                    onButtonEvent("MOUSE_LEFT", "up")
                    onButtonEvent("MOUSE_LEFT", "down")
                    onButtonEvent("MOUSE_LEFT", "up")
                }
            )

            // Left-Click Drag Lock Toggle
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
                    .weight(1.1f)
                    .fillMaxHeight(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (isDragLocked) AccentAmber else BgElevated,
                    contentColor = if (isDragLocked) BgPrimary else TextPrimary
                ),
                shape = RoundedCornerShape(10.dp),
                border = if (!isDragLocked) androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle) else null,
                contentPadding = PaddingValues(horizontal = 4.dp, vertical = 4.dp)
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = if (isDragLocked) "DRAG LOCKED" else "Drag Lock",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = if (isDragLocked) "Tap to Drop" else "Hold to Move",
                        fontSize = 9.sp,
                        color = if (isDragLocked) BgPrimary.copy(alpha = 0.8f) else TextSecondary
                    )
                }
            }

            // Hardware DPI Cycle Switcher
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
                shape = RoundedCornerShape(10.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle),
                contentPadding = PaddingValues(horizontal = 4.dp, vertical = 4.dp)
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("DPI SPEED", fontSize = 9.sp, color = TextSecondary)
                    Text(
                        text = dpiLevels[currentDpiIndex],
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = AccentCyan
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        // --- 4. Bottom Controls: Lift Clutch & Neutral Recenter ---
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(48.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            // Clutch (Lift Mouse / Move Toggle)
            Button(
                onClick = onToggleFreeze,
                modifier = Modifier
                    .weight(1.3f)
                    .fillMaxHeight(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (isMotionFrozen) AccentAmber else BgElevated,
                    contentColor = if (isMotionFrozen) BgPrimary else TextPrimary
                ),
                shape = RoundedCornerShape(12.dp),
                border = if (!isMotionFrozen) androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle) else null
            ) {
                Text(
                    text = if (isMotionFrozen) "Pointer Paused" else "Lift Clutch",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            // Neutral Calibration Recenter
            Button(
                onClick = onRecenter,
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = AccentGreen,
                    contentColor = BgPrimary
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("Recenter", fontSize = 13.sp, fontWeight = FontWeight.Bold)
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
    fontSize: androidx.compose.ui.unit.TextUnit = 14.sp,
    onButtonEvent: (state: String) -> Unit
) {
    val view = LocalView.current
    var isPressed by remember { mutableStateOf(false) }

    val curBg = if (isPressed) AccentCyan else accentColor
    val curTextColor = if (isPressed) BgPrimary else textColor

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(14.dp))
            .background(curBg)
            .then(
                if (borderColor != null && !isPressed) Modifier.border(1.5.dp, borderColor, RoundedCornerShape(14.dp))
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
            modifier = Modifier.padding(horizontal = 6.dp)
        ) {
            Text(
                text = label,
                color = curTextColor,
                fontSize = fontSize,
                fontWeight = FontWeight.Bold
            )
            if (sublabel != null) {
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = sublabel,
                    color = curTextColor.copy(alpha = 0.7f),
                    fontSize = 10.sp
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
            .clip(RoundedCornerShape(14.dp))
            .background(if (isWheelPressed) AccentCyan.copy(alpha = 0.25f) else BgElevated)
            .border(1.5.dp, if (isWheelPressed) AccentCyan else BorderSubtle, RoundedCornerShape(14.dp))
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
                        onScroll(true) // Scroll Up
                        accumulatedDrag = 0f
                    } else if (accumulatedDrag >= dragThreshold) {
                        view.performHapticFeedback(HapticFeedbackConstants.CLOCK_TICK)
                        onScroll(false) // Scroll Down
                        accumulatedDrag = 0f
                    }
                }
            },
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.padding(vertical = 8.dp)
        ) {
            Text("▲", color = AccentCyan, fontSize = 12.sp)
            Spacer(modifier = Modifier.height(4.dp))

            // Simulated Wheel Tread
            Column(
                modifier = Modifier
                    .width(28.dp)
                    .height(36.dp)
                    .clip(RoundedCornerShape(6.dp))
                    .background(Color(0xFF0F0F16))
                    .border(1.dp, BorderSubtle, RoundedCornerShape(6.dp))
                    .padding(vertical = 4.dp),
                verticalArrangement = Arrangement.SpaceEvenly,
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                repeat(4) {
                    Box(
                        modifier = Modifier
                            .width(18.dp)
                            .height(2.5.dp)
                            .background(if (isWheelPressed) AccentCyan else TextSecondary.copy(alpha = 0.4f))
                    )
                }
            }

            Spacer(modifier = Modifier.height(4.dp))
            Text("WHEEL", color = TextSecondary, fontSize = 9.sp, fontWeight = FontWeight.Bold)
            Text("CLICK", color = TextSecondary.copy(alpha = 0.6f), fontSize = 8.sp)
            Spacer(modifier = Modifier.height(2.dp))
            Text("▼", color = AccentCyan, fontSize = 12.sp)
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
    fontSize: androidx.compose.ui.unit.TextUnit = 12.sp,
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
        shape = RoundedCornerShape(10.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle),
        contentPadding = PaddingValues(horizontal = 6.dp, vertical = 6.dp)
    ) {
        Text(text = label, fontSize = fontSize, fontWeight = FontWeight.SemiBold)
    }
}
