<script setup>
import { ref, onMounted } from 'vue'

const searchQuery = ref('')
const searchResults = ref([])
const hasSearched = ref(false)
const searchInput = ref(null)

const handleSearch = async (event) => {
  const rawValue = event && event.target ? event.target.value : searchQuery.value;
  const cleanQuery = rawValue.trim().toUpperCase();
  
  if (!cleanQuery) return;
  
  hasSearched.value = true;
  
  // 1. INSTANTLY clear the input box so the next tag in the rapid-fire queue has a blank slate
  searchQuery.value = '';
  if (event && event.target) event.target.value = '';
  
  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(cleanQuery)}`)
    
    if (!response.ok) {
      console.error(`⚠️ BACKEND REJECTED: ${response.status}`);
      return;
    }

    const incomingData = await response.json()
    
    // 2. If the database found the asset, add it to our visual list!
    // 2. If the database found assets, loop through ALL of them!
    if (incomingData.length > 0) {
      
      // We reverse it so the most recently seen items stay at the very top of your screen
      incomingData.reverse().forEach(newAsset => {
        
        // 3. Still prevent duplicates!
        const alreadyOnScreen = searchResults.value.some(asset => asset.epc === newAsset.epc);
        
        if (!alreadyOnScreen) {
          searchResults.value.unshift(newAsset); 
        }
      });
    }
    
  } catch (error) {
    console.error(`❌ FATAL ERROR: ${error.message}`);
  }
}

const clearScreen = () => {
  searchResults.value = [];
  hasSearched.value = false;
  searchInput.value?.focus(); // Put the cursor back in the box
}

onMounted(() => {
  searchInput.value?.focus()
})
</script>

<template>
  <div class="lookup-container">
    <h2>Asset Lookup</h2>
    
    <div class="search-box">
      <input 
        ref="searchInput"
        v-model="searchQuery" 
        @keyup.enter="handleSearch"
        type="text" 
        placeholder="Scan a tag or type an asset name..." 
        autofocus
      />
      <button @click="handleSearch">Search</button>
      <button @click="clearScreen" style="background-color: #6c757d;">Clear</button>
    </div>

    <div v-if="hasSearched && searchResults.length === 0" class="no-results">
      <p>❌ No assets found matching "{{ searchQuery }}"</p>
    </div>

    <div v-if="searchResults.length > 0" class="results-grid">
      <div v-for="asset in searchResults" :key="asset.id" class="asset-card">
        <h3>{{ asset.name || 'Unknown Asset' }}</h3>
        
        <div class="status-banner" :class="asset.status === 'PRESENT' ? 'bg-green' : 'bg-red'">
          {{ asset.status }}
        </div>
        
        <div class="details">
          <p><strong>📍 Last Room:</strong> {{ asset.room || 'Unknown' }}</p>
          <p><strong>🕒 Last Seen:</strong> {{ new Date(asset.last_seen).toLocaleString() }}</p>
          <p class="epc-text">EPC: {{ asset.epc }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lookup-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  text-align: center;
}

.search-box {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-bottom: 40px;
}

input {
  width: 70%;
  padding: 15px;
  font-size: 1.2rem;
  border: 2px solid #ccc;
  border-radius: 8px;
}

button {
  padding: 15px 30px;
  font-size: 1.2rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

button:hover {
  background-color: #0056b3;
}

.results-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.asset-card {
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 20px;
  background: #fff;
  color: #333; /* <-- ADD THIS LINE */
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.asset-card h3 {
  margin-top: 0;
  font-size: 1.5rem;
}

.status-banner {
  padding: 10px;
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  border-radius: 6px;
  margin: 15px 0;
}

.bg-green { background-color: #28a745; }
.bg-red { background-color: #dc3545; }

.details p {
  font-size: 1.1rem;
  margin: 5px 0;
}

.epc-text {
  margin-top: 15px !important;
  font-family: monospace;
  color: #888;
  font-size: 0.9rem !important;
}

.no-results {
  font-size: 1.2rem;
  color: #666;
  margin-top: 20px;
}
</style>