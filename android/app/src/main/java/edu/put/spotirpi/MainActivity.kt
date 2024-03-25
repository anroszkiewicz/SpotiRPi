package edu.put.spotirpi

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothSocket
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.TextView
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import java.io.IOException
import java.util.UUID


class MainActivity : ComponentActivity() {
    private lateinit var socket: BluetoothSocket
    private val PERMISSION_CODE: Int = 111
    private var uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
    private var bluetoothAdapter: BluetoothAdapter? = null
    private var first = true

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val bluetoothManager: BluetoothManager = getSystemService(BluetoothManager::class.java)
        bluetoothAdapter = bluetoothManager.adapter
        if (bluetoothAdapter == null) {
            Toast.makeText(applicationContext, "No bluetooth device", Toast.LENGTH_LONG).show()
        }
        connect()
    }

    fun listenClick(v: View) {
        send("L")
    }

    fun listenClickPl(v: View) {
        send("F")
    }

    fun plusClick(v: View) {
        send("P")
    }

    fun minusClick(v: View) {
        send("M")
    }

    fun playClick(v: View) {
        send("S")
    }
    private fun send(command: String) {
        Log.e("ups", "here")
        if (ContextCompat.checkSelfPermission(
                baseContext,
                Manifest.permission.BLUETOOTH_CONNECT
            )
            != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.BLUETOOTH_CONNECT),
                PERMISSION_CODE
            )
        }
        //if (connect() != null)
        while(first) connect()
        val stream = socket.outputStream
        try {
            Log.e("ups", "send")
            stream.write(command.toByteArray())
            stream.flush()
            //stream.close()
            //socket.close()
        } catch (_: IOException) {
            stream.close()
            socket.close()
            Log.e("ups", "send failed")
            if(connect()!= null) send(command)
        }
    }

    private fun connect(): BluetoothSocket? {
        findViewById<TextView>(R.id.status).text = "connecting..."
        if (ContextCompat.checkSelfPermission(
                baseContext,
                Manifest.permission.BLUETOOTH_CONNECT
            )
            != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.BLUETOOTH_CONNECT),
                PERMISSION_CODE
            )
        }
        val pairedDevices: Set<BluetoothDevice>? = bluetoothAdapter?.bondedDevices
        var device: BluetoothDevice? = null
        pairedDevices?.forEach { dev ->
            val deviceName = dev.name
            if (deviceName == "raspberrypi") device = dev
        }
        if (device == null) {
            Toast.makeText(this, "No device found", Toast.LENGTH_LONG).show()
            findViewById<TextView>(R.id.status).text = "no device found"
            return null
        } else {
            socket = device!!.createRfcommSocketToServiceRecord(uuid)
            first = false
            try {
                Log.e("ups", "connect")
                socket.connect()
            } catch (_: IOException) {
                Log.e("ups", "connect failed")
                socket.close()
                return connect()
            }
        }
        findViewById<TextView>(R.id.status).text = "connected"
        return socket
    }
}
