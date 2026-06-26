<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { io } from 'socket.io-client'

const events = ref([])
let socket;

const fetchEvents = async () => {
  try {
    const response = await fetch(`/api/events`)
    events.value = await response.json()
  } catch (error) {
    console.error('Error fetching events:', error)
  }
}

onMounted(() => {
  fetchEvents() // Initial load
  
  // Connect to the Socket server and listen for updates
  socket = io()
  socket.on('new_scan_event', () => {
    console.log("Live update received! Refreshing log...")
    fetchEvents()
  })
})

onUnmounted(() => {
  if (socket) socket.disconnect()
})
</script>

<template>
  <div>
    <h2>Recent Scan Logs</h2>
    <table>
      <thead>
        <tr>
          <th>Time</th>
          <th>Asset Name</th>
          <th>Room / Zone</th>
          <th>Tag ID (EPC)</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="event in events" :key="event.id">
          <td>{{ new Date(event.timestamp).toLocaleString() }}</td>
          <td><strong>{{ event.name || 'Unknown Asset' }}</strong></td>
          <td>{{ event.room || '—' }}</td>
          <td class="epc-col">{{ event.epc }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
  h2 {
    text-align: center;
    margin-bottom: 20px;
  }

  table {
    margin: 0 auto; 
    width: 90%;
    border-collapse: collapse;
    background-color: white;
    color: black;
  }

  th {
    background-color: rgb(192, 191, 191);
    border: 1px solid #cccccc;
    padding: 10px;
  }

  td {
    text-align: center;
    border: 1px solid #cccccc;
    padding: 8px;
  }

  td:hover {
    background-color: rgb(214, 212, 212);
  }

  tbody tr:nth-child(odd) {
    background-color: rgb(245, 243, 243);
  }

  .epc-col {
    font-family: monospace;
    color: #555;
  }
</style>