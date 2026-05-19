<script>
import ContextCard from './ContextCard.vue';

export default {
  data() {
    return {
      collapse: false,
      cards: [],
      name: '',
      content: '',
      keywords: '',
      selected_type: 'all',
      type: 'other',
      // Type-specific values:
      parent_location: '',
      child_locations: '',
      equipped: false,
      create_memories: true
    }
  },
  components: { ContextCard },
  methods: {
    // Add card with id, name, content, keywords (comma separated),
    // and type-specific values.
    addCard() {
      const type = this.type
      var payload = {
        id: Date.now(),
        name: this.name,
        type: type,
        content: this.content,
        
      };
      if (type === 'location' && this.parent_location?.trim()) {
        payload.parent_location = this.parent_location;
      }
      if (type === 'location' && this.child_locations?.trim()) {
        payload.child_locations = this.child_locations;
      }
      if (type === 'character' && this.create_memories) {
        payload.create_memories = this.create_memories;
      }
      payload.keywords = this.keywords.split(',')
      
      this.cards.push(payload);
      this.name = '';
      this.content = '';
      this.keywords = '';
    },
    // Get matching context cards based on keywords in recent story content
    getMatchingContextCards(text) {
      const lower_text = text.toLowerCase();
      const matching = [];

      for (const card of this.cards) {
        if (card.keywords.length === 0) continue; // skip empty keyword fields

        // Check if any keyword is in the text
        for (const keyword of card.keywords) {
          if (lower_text.includes(keyword.trim().toLowerCase())) {
            payload = {
              name: card.name || '',
              type: card.type || '',
              content: card.content || '',
              parent_location: card.parent_location || '',
              child_locations: card.child_locations || ''
            };
            matching.push(payload);
            break; // Only add card once even if multiple keywords match
          }
        }
        // To avoid adding too much context, stop if we have 10 matching cards
        if (matching.length >= 10) {
          break;
        }
      }

      if (matching.length === 0) return '';
      
      // Format matching cards into a string to be included in the prompt.
      // Example format
      // "Colin, character:
      //  A talented swordsman."
      let card_text = '';
      for (const card of matching) {
        card_text += card.name + ', ';

        card_text += card.type;

        if (card.parent_location) {
          card_text += ' in ' + card.parent_location;
        }
        card_text += ':\n' + card.content + '\n';
        if (card.child_locations) {
          card_text += 'Locations within ' + card.name + ': ' + card.child_locations + '\n';
        }
        card_text += '\n';
      }
      return card_text;
    },
    removeCard(id) {
      this.cards = this.cards.filter(card => card.id !== id);
    }
  },
  computed: {
    // Display cards from newest to oldest, filtered by selected type
    sortedCards() {
      let filtered = this.cards;
      if (this.selected_type !== 'all') {
        filtered = filtered.filter(card => card.type === this.selected_type);
      }
      return [...filtered].reverse();
    }
  }
}
</script>

<template>
  <div class="context-cards">
    <h2>Add New Card</h2>
    <button @click="collapse = !collapse">{{ collapse ? 'Expand' : 'Collapse' }}</button>

    <div class="context-card" v-if="!collapse">
      <h4>Name</h4>
      <input type="text" v-model="name" maxlength="50" />

      <label>Type: 
        <select v-model="type">
          <option value="other">Other</option>
          <option value="character">Character</option>
          <option value="location">Location</option>
          <option value="object">Object</option>
        </select>
      </label>

      <!-- Type-specific values -->
      <div v-if="type === 'character'">
        <label>Create Character Memories: </label>
        <input v-model="create_memories" type="checkbox" class="custom-checkbox" />
      </div>

      <div v-if="type === 'location'">
        <label>Parent Location:</label>
        <input type="text" v-model="parent_location" maxlength="200" />
      </div>
      <div v-if="type === 'location'">
        <label>Child Locations (comma-seperated):</label>
        <input type="text" v-model="child_locations" maxlength="200" />
      </div>

      <h4>Content</h4>
      <textarea v-model="content" />

      <h4>Keywords (comma-separated)</h4>
      <input type="text" v-model="keywords" maxlength="200" />

      <button @click="addCard">Add Card</button>
    </div>
    <div class="info-container">
    <h3>Existing Cards</h3>
    <h4>
      Cards with keywords matching recent story content will be included as context in story generation.
      Cards will automatically be saved when edited.
    </h4>
    </div>
    <label>Filter: 
      <select v-model="selected_type">
        <option value="all">All</option>
        <option value="character">Characters</option>
        <option value="location">Locations</option>
        <option value="object">Object</option>
        <option value="other">Other</option>
      </select>
    </label>
    <ContextCard
      v-for="card in sortedCards"
      :key="card.id"
      :card="card"
      @remove="removeCard(card.id)"
    />
  </div>
</template>

<style>
.context-cards {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.context-cards > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.context-card {
  border: 1px solid #aa3bff;
  border-radius: 5px;
  padding: 5px;
  background: #1a1a2e;
  color: #fff;
}
.context-card h4 {
  margin: 3px 0 3px;
}
.context-card textarea {
  min-height: 120px;
}
.context-card button {
  margin-bottom: 10px;
}
</style>