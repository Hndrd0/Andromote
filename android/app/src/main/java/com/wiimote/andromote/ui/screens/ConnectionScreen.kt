package com.wiimote.andromote.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.wiimote.andromote.model.ConnectionState
import com.wiimote.andromote.model.DiscoveredServer
import com.wiimote.andromote.ui.theme.*

@Composable
fun ConnectionScreen(
    connectionState: ConnectionState,
    discoveredServers: List<DiscoveredServer>,
    isScanning: Boolean,
    onScan: () -> Unit,
    onConnectServer: (ip: String, tcpPort: Int, motionPort: Int) -> Unit,
    onSubmitPin: (String) -> Unit,
    onDisconnect: () -> Unit
) {
    var manualIp by remember { mutableStateOf("") }
    var pinInput by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Title
        Text(
            text = "Connect to Windows PC",
            color = TextPrimary,
            fontSize = 22.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 12.dp)
        )

        // Connection Status Banner
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = SurfaceDark),
            shape = RoundedCornerShape(12.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(14.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = when {
                            connectionState.isConnected -> "Status: Connected"
                            connectionState.isConnecting -> "Status: Connecting..."
                            else -> "Status: Disconnected"
                        },
                        color = when {
                            connectionState.isConnected -> AccentGreen
                            connectionState.isConnecting -> AccentAmber
                            else -> TextSecondary
                        },
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp
                    )
                    if (connectionState.isConnected) {
                        Text(
                            text = "PC: ${connectionState.serverIp} (${connectionState.latencyMs.toInt()} ms)",
                            color = TextSecondary,
                            fontSize = 12.sp
                        )
                    }
                }

                if (connectionState.isConnected) {
                    Button(
                        onClick = onDisconnect,
                        colors = ButtonDefaults.buttonColors(containerColor = AccentRed),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Text("Disconnect")
                    }
                }
            }
        }

        connectionState.errorMessage?.let { err ->
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = err, color = AccentRed, fontSize = 13.sp)
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Discovered PCs Section
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Discovered PCs on Wi-Fi",
                color = AccentCyan,
                fontWeight = FontWeight.SemiBold,
                fontSize = 15.sp
            )

            IconButton(onClick = onScan, enabled = !isScanning) {
                Icon(
                    imageVector = androidx.compose.material.icons.Icons.Default.Refresh,
                    contentDescription = "Scan for PCs",
                    tint = AccentCyan
                )
            }
        }

        if (isScanning) {
            LinearProgressIndicator(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                color = AccentCyan
            )
        }

        if (discoveredServers.isEmpty() && !isScanning) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(90.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(SurfaceDark),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "No PCs discovered automatically.\nMake sure Andromote Receiver is running on PC.",
                    color = TextSecondary,
                    fontSize = 13.sp,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center
                )
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 180.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(discoveredServers) { srv ->
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onConnectServer(srv.ip, srv.tcpPort, srv.motionPort) },
                        colors = CardDefaults.cardColors(containerColor = SurfaceDark),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(12.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(
                                    imageVector = androidx.compose.material.icons.Icons.Default.Share,
                                    contentDescription = "PC Node",
                                    tint = AccentCyan
                                )
                                Spacer(modifier = Modifier.width(10.dp))
                                Column {
                                    Text(text = srv.hostname, color = TextPrimary, fontWeight = FontWeight.Bold)
                                    Text(text = "${srv.ip}:${srv.tcpPort}", color = TextSecondary, fontSize = 12.sp)
                                }
                            }
                            Button(
                                onClick = { onConnectServer(srv.ip, srv.tcpPort, srv.motionPort) },
                                shape = RoundedCornerShape(6.dp)
                            ) {
                                Text("Connect")
                            }
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Manual IP Entry
        Text(
            text = "Manual IP Entry",
            color = AccentCyan,
            fontWeight = FontWeight.SemiBold,
            fontSize = 15.sp,
            modifier = Modifier.align(Alignment.Start)
        )
        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            value = manualIp,
            onValueChange = { manualIp = it },
            label = { Text("PC IP Address (e.g. 192.168.1.100)") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = TextPrimary,
                unfocusedTextColor = TextPrimary,
                focusedBorderColor = AccentCyan,
                unfocusedBorderColor = BorderSubtle
            )
        )

        Spacer(modifier = Modifier.height(8.dp))

        Button(
            onClick = {
                if (manualIp.isNotBlank()) {
                    onConnectServer(manualIp.trim(), 42425, 42426)
                }
            },
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(8.dp)
        ) {
            Text("Connect Directly")
        }

        // Pairing PIN Dialog
        if (connectionState.needsPairingPin) {
            AlertDialog(
                onDismissRequest = {},
                title = { Text("Enter 4-Digit Pairing PIN", color = TextPrimary) },
                text = {
                    Column {
                        Text(
                            text = "Enter the pairing code shown on your Windows PC receiver screen:",
                            color = TextSecondary,
                            fontSize = 13.sp
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        OutlinedTextField(
                            value = pinInput,
                            onValueChange = { if (it.length <= 4) pinInput = it },
                            placeholder = { Text("4-digit PIN") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                },
                confirmButton = {
                    Button(
                        onClick = {
                            if (pinInput.length == 4) {
                                onSubmitPin(pinInput)
                                pinInput = ""
                            }
                        }
                    ) {
                        Text("Pair Device")
                    }
                },
                dismissButton = {
                    TextButton(onClick = onDisconnect) {
                        Text("Cancel")
                    }
                },
                containerColor = SurfaceDark
            )
        }
    }
}
