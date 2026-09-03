package com.wiimote.andromote.ui.components

import android.view.HapticFeedbackConstants
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.waitForUpOrCancellation
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
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

@Composable
fun WiiRemotePad(
    modifier: Modifier = Modifier,
    isLandscape: Boolean = false,
    onButtonEvent: (button: String, state: String) -> Unit
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .padding(8.dp),
        contentAlignment = Alignment.Center
    ) {
        // Wii Remote Body
        val bodyModifier = if (isLandscape) {
            Modifier
                .fillMaxWidth(0.92f)
                .height(300.dp)
        } else {
            Modifier
                .width(260.dp)
                .fillMaxHeight(0.96f)
        }

        Box(
            modifier = bodyModifier
                .shadow(16.dp, RoundedCornerShape(32.dp))
                .clip(RoundedCornerShape(32.dp))
                .background(WiimoteBody)
                .border(2.dp, WiimoteBorder, RoundedCornerShape(32.dp))
                .padding(16.dp)
        ) {
            if (isLandscape) {
                LandscapeLayout(onButtonEvent = onButtonEvent)
            } else {
                PortraitLayout(onButtonEvent = onButtonEvent)
            }
        }
    }
}

@Composable
private fun PortraitLayout(onButtonEvent: (String, String) -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        // Top Bar: Player 1 LED indicator
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            repeat(4) { idx ->
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .clip(CircleShape)
                        .background(if (idx == 0) AccentCyan else Color.LightGray)
                )
                if (idx < 3) Spacer(modifier = Modifier.width(12.dp))
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // D-Pad
        DPadControl(onButtonEvent = onButtonEvent)

        Spacer(modifier = Modifier.height(12.dp))

        // Large 'A' Button
        TactileButton(
            label = "A",
            buttonId = "A",
            modifier = Modifier.size(72.dp),
            fontSize = 28.sp,
            isRound = true,
            onButtonEvent = onButtonEvent
        )

        Spacer(modifier = Modifier.height(12.dp))

        // Trigger 'B' Button (on-screen ergonomic secondary button)
        TactileButton(
            label = "B (Trigger)",
            buttonId = "B",
            modifier = Modifier
                .fillMaxWidth(0.8f)
                .height(44.dp),
            fontSize = 16.sp,
            isRound = false,
            onButtonEvent = onButtonEvent
        )

        Spacer(modifier = Modifier.height(12.dp))

        // Center Cluster: Minus (-), Home, Plus (+)
        Row(
            modifier = Modifier.fillMaxWidth(0.85f),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            TactileButton(label = "—", buttonId = "MINUS", modifier = Modifier.size(40.dp), isRound = true, onButtonEvent = onButtonEvent)
            TactileButton(
                label = "🏠",
                buttonId = "HOME",
                modifier = Modifier.size(44.dp),
                isRound = true,
                accentColor = PrimaryBlue,
                onButtonEvent = onButtonEvent
            )
            TactileButton(label = "+", buttonId = "PLUS", modifier = Modifier.size(40.dp), isRound = true, onButtonEvent = onButtonEvent)
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Lower Cluster: '1' and '2' buttons
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            TactileButton(label = "1", buttonId = "1", modifier = Modifier.size(42.dp), isRound = true, onButtonEvent = onButtonEvent)
            TactileButton(label = "2", buttonId = "2", modifier = Modifier.size(42.dp), isRound = true, onButtonEvent = onButtonEvent)
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Speaker grille dots
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center
        ) {
            repeat(3) {
                Box(
                    modifier = Modifier
                        .size(5.dp)
                        .clip(CircleShape)
                        .background(Color.Gray.copy(alpha = 0.4f))
                )
                Spacer(modifier = Modifier.width(6.dp))
            }
        }
    }
}

@Composable
private fun LandscapeLayout(onButtonEvent: (String, String) -> Unit) {
    Row(
        modifier = Modifier.fillMaxSize(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        // Left section: D-Pad
        Box(
            modifier = Modifier.weight(1f),
            contentAlignment = Alignment.Center
        ) {
            DPadControl(onButtonEvent = onButtonEvent)
        }

        // Center section: Minus, Home, Plus & Triggers
        Column(
            modifier = Modifier.weight(1f),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Row(
                horizontalArrangement = Arrangement.spacedBy(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                TactileButton(label = "—", buttonId = "MINUS", modifier = Modifier.size(40.dp), isRound = true, onButtonEvent = onButtonEvent)
                TactileButton(label = "🏠", buttonId = "HOME", modifier = Modifier.size(46.dp), isRound = true, accentColor = PrimaryBlue, onButtonEvent = onButtonEvent)
                TactileButton(label = "+", buttonId = "PLUS", modifier = Modifier.size(40.dp), isRound = true, onButtonEvent = onButtonEvent)
            }
            Spacer(modifier = Modifier.height(16.dp))
            TactileButton(label = "B Trigger", buttonId = "B", modifier = Modifier.width(140.dp).height(40.dp), isRound = false, onButtonEvent = onButtonEvent)
        }

        // Right section: A, 1, 2
        Row(
            modifier = Modifier.weight(1f),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically
        ) {
            TactileButton(label = "A", buttonId = "A", modifier = Modifier.size(72.dp), fontSize = 28.sp, isRound = true, onButtonEvent = onButtonEvent)
            Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
                TactileButton(label = "1", buttonId = "1", modifier = Modifier.size(42.dp), isRound = true, onButtonEvent = onButtonEvent)
                TactileButton(label = "2", buttonId = "2", modifier = Modifier.size(42.dp), isRound = true, onButtonEvent = onButtonEvent)
            }
        }
    }
}

@Composable
fun DPadControl(onButtonEvent: (String, String) -> Unit) {
    val dpadSize = 135.dp
    val armWidth = 45.dp

    Box(
        modifier = Modifier
            .size(dpadSize)
            .shadow(4.dp, RoundedCornerShape(12.dp))
            .clip(RoundedCornerShape(12.dp))
            .background(WiimoteDpad),
        contentAlignment = Alignment.Center
    ) {
        // D-pad Up
        Box(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .size(armWidth)
        ) {
            DPadButton(label = "▲", buttonId = "DPAD_UP", onButtonEvent = onButtonEvent)
        }

        // D-pad Down
        Box(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .size(armWidth)
        ) {
            DPadButton(label = "▼", buttonId = "DPAD_DOWN", onButtonEvent = onButtonEvent)
        }

        // D-pad Left
        Box(
            modifier = Modifier
                .align(Alignment.CenterStart)
                .size(armWidth)
        ) {
            DPadButton(label = "◀", buttonId = "DPAD_LEFT", onButtonEvent = onButtonEvent)
        }

        // D-pad Right
        Box(
            modifier = Modifier
                .align(Alignment.CenterEnd)
                .size(armWidth)
        ) {
            DPadButton(label = "▶", buttonId = "DPAD_RIGHT", onButtonEvent = onButtonEvent)
        }

        // Center Pivot
        Box(
            modifier = Modifier
                .size(16.dp)
                .clip(CircleShape)
                .background(Color(0xFF334155))
        )
    }
}

@Composable
fun DPadButton(
    label: String,
    buttonId: String,
    onButtonEvent: (String, String) -> Unit
) {
    var isPressed by remember { mutableStateOf(false) }
    val view = LocalView.current

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(if (isPressed) WiimoteDpadPressed else Color.Transparent)
            .pointerInput(buttonId) {
                awaitEachGesture {
                    awaitFirstDown()
                    isPressed = true
                    view.performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY)
                    onButtonEvent(buttonId, "down")

                    waitForUpOrCancellation()
                    isPressed = false
                    onButtonEvent(buttonId, "up")
                }
            },
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = label,
            color = if (isPressed) AccentCyan else Color.White,
            fontSize = 15.sp,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
fun TactileButton(
    label: String,
    buttonId: String,
    modifier: Modifier = Modifier,
    fontSize: androidx.compose.ui.unit.TextUnit = 18.sp,
    isRound: Boolean = true,
    accentColor: Color? = null,
    onButtonEvent: (String, String) -> Unit
) {
    var isPressed by remember { mutableStateOf(false) }
    val view = LocalView.current

    val shape = if (isRound) CircleShape else RoundedCornerShape(12.dp)
    val bgColor = if (isPressed) {
        WiimoteButtonPressed
    } else {
        accentColor ?: WiimoteButtonNormal
    }

    Box(
        modifier = modifier
            .shadow(if (isPressed) 1.dp else 4.dp, shape)
            .clip(shape)
            .background(bgColor)
            .border(1.5.dp, WiimoteBorder, shape)
            .pointerInput(buttonId) {
                awaitEachGesture {
                    awaitFirstDown()
                    isPressed = true
                    view.performHapticFeedback(HapticFeedbackConstants.VIRTUAL_KEY)
                    onButtonEvent(buttonId, "down")

                    waitForUpOrCancellation()
                    isPressed = false
                    onButtonEvent(buttonId, "up")
                }
            },
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = label,
            color = if (accentColor != null) Color.White else WiimoteText,
            fontSize = fontSize,
            fontWeight = FontWeight.ExtraBold
        )
    }
}
