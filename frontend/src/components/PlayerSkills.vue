<script>
import Skills from './PlayerSkills.vue';

export default {
  data() {
    return {
      collapse: false,
      name: '',
      content: '',
      experience: 0,
      level: 0,
      skills: []
    }
  },
  components: { Skills },
  methods: {
    // Add skill with id, name, content, experience, and level
    addSkill() {
      const type = this.type

      // Perishables cannot be equipped, only used
      if (type === 'perishable') {
        this.equipped = false;
      }
      let payload = {
        id: Date.now(),
        name: this.name,
        type: type,
        content: this.content,
        equipped: this.equipped
      };
      this.skills.push(payload);
      this.name = '';
      this.content = '';
    },
    getSkills() {
      return this.skills;
    },
    getSkillsStr() {
      if (this.skills.length === 0) return '';

      let str = '[Player Skills]';
      const grouped = {};

      for (const skill of this.skills) {
        str += title + '\n';
        str += `- ${skill.name}, level: ${skill.level}\n`;
      }

      return str;
    },
    removeSkill(id) {
      this.skills = this.skills.filter(skill => skill.id !== id);
    }
  },
  computed: {
    // Display skills from newest to oldest
    sortedSkills() {
      let filtered = this.skills;
      return [...filtered].reverse();
    }
  }
}
</script>

<template>
  <div class="header-row">
    <h2>Add Skill</h2>
    <button @click="collapse = !collapse">{{ collapse ? 'Expand' : 'Collapse' }}</button>
  </div>

  <div class="container">    
    <div class="skill" v-if="!collapse">
      <h4>Skill Name</h4>
      <input type="text" v-model="name" maxlength="25" />
      
      <label>Level (0-10): 
        <input type="number" v-model="level" min="0" max="10" />
        <span title="Card name and type will be used in content generation.">
          ⓘ
        </span>
      </label>

      <h4>skill Information</h4>
      <textarea v-model="content" />

      <button @click="addSkill">Add skill</button>
    </div>
  </div>

  <div class="container">
    <p v-if="sortedSkills.length === 0">
      No Skills.
    </p>

    <Skill
      v-for="skill in sortedSkills"
      :key="skill.id"
      :skill="skill"
      @remove="removeSkill(skill.id)"
    />
  </div>
</template>

<style>
.skills {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.skills > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.skill {
  border: 1px solid #aa3bff;
  border-radius: 5px;
  padding: 5px;
  background: #1a1a2e;
  color: #fff;
}
.skill h4 {
  margin: 3px 0 3px;
}
.skill textarea {
  min-height: 120px;
}
.skill button {
  margin-bottom: 10px;
}
</style>