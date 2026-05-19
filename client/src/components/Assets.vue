<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { io } from 'socket.io-client'

const assets = ref([])
let socket;

const fetchAssets = async () => {
  try {
    const response = await fetch('http://localhost:3000/api/assets')
    assets.value = await response.json()
  } catch (error) {
    console.error('Error fetching assets:', error)
  }
}

onMounted(() => {
  fetchAssets() // Initial load
  
  // Connect to the Socket server and listen for updates
  socket = io('http://localhost:3000')
  socket.on('new_scan_event', () => {
    console.log("Live update received! Refreshing table...")
    fetchAssets()
  })
})

onUnmounted(() => {
  if (socket) socket.disconnect()
})
</script>

<template>
  <div>
    <h2>Office Inventory (Πάγια)</h2>
    <table>
      <thead>
        <tr>
          <th>EPC (Tag ID)</th>
          <th>Asset Name</th>
          <th>Room / Zone</th>
          <th>Status</th>
          <th>Last Seen</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="asset in assets" :key="asset.id">
          <td>{{ asset.epc }}</td>
          <td>{{ asset.name || 'Unknown Asset' }}</td>
          <td>{{ asset.room || '—' }}</td>
          <td>
            <span :class="{'status-present': asset.status === 'PRESENT', 'status-missing': asset.status === 'MISSING'}">
              {{ asset.status }}
            </span>
          </td>
          <td>{{ new Date(asset.last_seen).toLocaleString() }}</td>
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

  .status-present {
    color: green;
    font-weight: bold;
  }
  
  .status-missing {
    color: red;
    font-weight: bold;
  }
</style>