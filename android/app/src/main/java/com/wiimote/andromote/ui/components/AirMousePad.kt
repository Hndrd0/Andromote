package com.wiimote.andromote.ui.components

import android.view.HapticFeedbackConstants
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.wiimote.andromote.ui.theme.*

/**
 * Air Mouse Pad:
 * High-precision motion-controlled air mouse interface with primary/secondary clicks,
 * touch scroll strip, double-click, presentation slide deck controls, and clutch freeze.
 */
@Composable
fun AirMousePad(
    isMotionFrozen: Boolean,
    onToggleFreeze: () -> Unit,
    onButtonEvent: (button: String, state: String) -> Unit,
    onRecenter: () -> Unit
) {
    var showPresentationControls by remember { mutableStateOf(true) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        // --- 1. Top Primary & Secondary Mouse Clicks ---
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(130.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Left Click (Large Primary)
            AirMouseButton(
                label = "LEFT CLICK",
                sublabel = "Select / Drag",
                modifier = Modifier
                    .weight(1.3f)
                    .fillMaxHeight(),
                accentColor = AccentCyan,
                textColor = BgPrimary,
                onButtonEvent = { state -> onButtonEvent("MOUSE_LEFT", state) }
            )

            // Right Click
            AirMouseButton(
                label = "RIGHT CLICK",
                sublabel = "Context Menu",
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight(),
                accentColor = BgElevated,
                textColor = TextPrimary,
                borderColor = BorderSubtle,
                onButtonEvent = { state -> onButtonEvent("MOUSE_RIGHT", state) }
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        // --- 2. Middle Action Bar: Scroll Strip, Middle Click, Double Click ---
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(110.dp),
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Touch Scroll Strip
            ScrollWheelStrip(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight(),
                onScroll = { isUp ->
                    val btn = if (isUp) "MOUSE_WHEEL_UP" else "MOUSE_WHEEL_DOWN"
                    onButtonEvent(btn, "down")
                    onButtonEvent(btn, "up")
                }
            )

            // Utility buttons column
            Column(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxHeight(),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Double Click Button
                AirMouseQuickButton(
                    label = "⚡ Double Click",
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    onClick = {
                        onButtonEvent("MOUSE_LEFT", "down")
                        onButtonEvent("MOUSE_LEFT", "up")
                        onButtonEvent("MOUSE_LEFT", "down")
                        onButtonEvent("MOUSE_LEFT", "up")
                    }
                )

                // Middle Click Button
                AirMouseButton(
                    label = "Middle Click",
                    sublabel = "Tab / Pan",
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    accentColor = BgElevated,
                    textColor = TextSecondary,
                    fontSize = 13.sp,
                    onButtonEvent = { state -> onButtonEvent("MOUSE_MIDDLE", state) }
                )
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        // --- 3. Presentation Controls Deck ---
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = BgSurface),
            shape = RoundedCornerShape(14.dp),
            border = androidx.compose.foundation.BorderStroke(1.dp, BorderSubtle)
        ) {
            Column(modifier = Modifier.padding(10.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "📊 Presentation Tools",
                        color = AccentCyan,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                    TextButton(
                        onClick = { showPresentationControls = !showPresentationControls },
                        contentPadding = PaddingValues(horizontal = 6.dp, vertical = 2.dp)
                    ) {
                        Text(
                            text = if (showPresentationControls) "Hide" else "Show",
                            color = TextTertiary,
                            fontSize = 11.sp
                        )
                    }
                }

                AnimatedVisibility(visible = showPresentationControls) {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        // Prev / Next slide buttons
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            AirMouseQuickButton(
                                label = "◀ Prev Slide",
                                modifier = Modifier.weight(1f),
                                onClick = {
                                    onButtonEvent("KEY_PAGEUP", "down")
                                    onButtonEvent("KEY_PAGEUP", "up")
                                }
                            )
                            AirMouseQuickButton(
                                label = "Next Slide ▶",
                                modifier = Modifier.weight(1f),
                                accentColor = AccentCyan,
                                textColor = BgPrimary,
                                onClick = {
                                    onButtonEvent("KEY_PAGEDOWN", "down")
                                    onButtonEvent("KEY_PAGEDOWN", "up")
                                }
                            )
                        }

                        // Auxiliary Slide Keys
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            AirMouseQuickButton(
                                label = "▶ Start (F5)",
                                modifier = Modifier.weight(1f),
                                fontSize = 11.sp,
                                onClick = {
                                    onButtonEvent("KEY_F5", "down")
                                    onButtonEvent("KEY_F5", "up")
                                }
                            )
                            AirMouseQuickButton(
                                label = "✕ Exit (Esc)",
                                modifier = Modifier.weight(1f),
                                fontSize = 11.sp,
                                onClick = {
                                    onButtonEvent("KEY_ESCAPE", "down")
                                    onButtonEvent("KEY_ESCAPE", "up")
                                }
                            )
                            AirMouseQuickButton(
                                label = "⬛ Blank",
                                modifier = Modifier.weight(0.8f),
                                fontSize = 11.sp,
                                onClick = {
                                    onButtonEvent("KEY_B", "down")
                                    onButtonEvent("KEY_B", "up")
                                }
                            )
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        // --- 4. Bottom Controls: Freeze Clutch & Recenter ---
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            // Clutch (Freeze / Move toggle)
            Button(
                onClick = onToggleFreeze,
                modifier = Modifier
                    .weight(1.4f)
                    .height(48.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (isMotionFrozen) AccentAmber else BgElevated,
                    contentColor = if (isMotionFrozen) BgPrimary else TextPrimary
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(
                    text = if (isMotionFrozen) "⏸️ Motion Paused" else "🖐️ Freeze Pointer",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            // Recenter
            Button(
                onClick = onRecenter,
                modifier = Modifier
                    .weight(1f)
                    .height(48.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = AccentGreen,
                    contentColor = BgPrimary
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("🎯 Recenter", fontSize = 13.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}

/**
 * Tactile Mouse Button with down/up state dispatch and haptics.
 */
@Composable
fun AirMouseButton(
    label: String,
    sublabel: String? = null,
    modifier: Modifier = Modifier,
    accentColor: Color = BgElevated,
    textColor: Color = TextPrimary,
    borderColor: Color = BorderSubtle,
    fontSize: androidx.compose.ui.unit.TextUnit = 16.sp,
    onButtonEvent: (state: String) -> Unit
) {
    var isPressed by remember { mutableStateOf(false) }
    val view = LocalView.current

    val bgColor = if (isPressed) AccentCyan else accentColor
    val curTextColor = if (isPressed) BgPrimary else textColor
    val curBorder = if (isPressed) AccentCyan else borderColor

    Box(
        modifier = modifier
            .shadow(if (isPressed) 2.dp else 6.dp, RoundedCornerShape(14.dp))
            .clip(RoundedCornerShape(14.dp))
            .background(bgColor)
            .border(1.5.dp, curBorder, RoundedCornerShape(14.dp))
            .pointerInput(label) {
                detectTapGestures(
                    onPress = {
                        isPressed = true
                        view.performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY)
                        onButtonEvent("down")
                        tryAwaitRelease()
                        isPressed = false
                        onButtonEvent("up")
                    }
                )
            },
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
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
        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 6.dp)
    ) {
        Text(text = label, fontSize = fontSize, fontWeight = FontWeight.SemiBold)
    }
}

/**
 * Vertical Touch Scroll Wheel Strip with drag gesture detection and haptics.
 */
@Composable
fun ScrollWheelStrip(
    modifier: Modifier = Modifier,
    onScroll: (isUp: Boolean) -> Unit
) {
    val view = LocalView.current
    var accumulatedDrag by remember { mutableStateOf(0f) }
    val dragThreshold = 22f

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(14.dp))
            .background(BgElevated)
            .border(1.5.dp, BorderSubtle, RoundedCornerShape(14.dp))
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
            verticalArrangement = Arrangement.Center
        ) {
            Text("▲", color = AccentCyan, fontSize = 14.sp)
            Spacer(modifier = Modifier.height(4.dp))
            Text("SCROLL", color = TextSecondary, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(4.dp))
            Text("▼", color = AccentCyan, fontSize = 14.sp)
        }
    }
}
