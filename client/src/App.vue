<script setup>

</script>

<template>
  <nav>
    <div class="bar">
      <router-link to="/events" class="tabs">Track Books</router-link>
      <router-link to="/assets" class="tabs">All Assets</router-link>
      <router-link to="/search" class="tabs">Search</router-link>
    </div>
  </nav>

  <main class="content">
    <router-view></router-view>
  </main>
</template>

<style scoped>
  nav {
    background-color: rgb(186, 189, 189);
  }

  .bar {
    display: flex;
    width: 100%;
    justify-content: center; /* Centers the whole group */
    gap: 50px; /* Puts an exact 50px gap between each tab */
  }

  .tabs {
    /* margin-left: 29%;  <-- REMOVED THIS */
    cursor: pointer;
    font-weight: bold;
    font-size: larger;
    padding: 15px;
    text-decoration: none; 
    color: #333; 
  }

  .tabs:hover {
    color: rgb(80, 80, 80);
  }

  .router-link-active {
    color: black;
    border-bottom: 3px solid rgb(35, 35, 36);
  }

  .content {
    padding: 20px;
  }
</style>
