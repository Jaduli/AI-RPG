<script>
import Skill from './PlayerSkill.vue';

export default {
  data() {
    return {
      collapse: false,
      name: '',
      level: 0,
      proficiency: '', // = level as a word, e.g. 'novice'
      skills: []
    }
  },
  components: { Skill },
  methods: {
    // Add skill with id, name, content, level, proficiency, and experience
    addSkill() {
      const level = this.level;
      const proficiency = this.levelToProficiency(level)

      const payload = {
        id: Date.now(),
        name: this.name,
        content: this.content,
        level,
        proficiency,
        experience: 0
      };
      this.skills.push(payload);
      this.name = '';
      this.content = '';
      this.level = 0;
      this.proficiency = '';
    },
    // Formats a level between 0 and 10 to a matching word.
    // Upgrades every 2 levels.
    levelToProficiency(level) {
      switch (true) {
        case level >= 0 && level < 2:
          return 'novice';
        case level >= 2 && level < 4:
          return 'beginner';
        case level >= 4 && level < 6:
          return 'intermediate';
        case level >= 6 && level < 8:
          return 'advanced';
        case level >= 8 && level < 10:
          return 'expert';
        case level === 10:
          return 'master';
        default:
          return 'unknown';
      }
    },
    // Returns xp required for level up.
    // Examples: 0->1 = 400, 1->2 = 606, 5->6 = 1566.
    // With this formula, it takes about (level + 2)
    // actions to level up. Some non-linear growth is
    // applied to make higher levels harder to obtain.
    // It should be noted that success gives higher xp gain,
    // making it easier to get xp on a higher levels.
    getLevelUpThreshold(level) {
      return Math.floor(400 + (level * 200) * (1 + level / 30));
    },
    // Adds xp to skill based on action outcome. Levels up 
    // skill if xp is over level up threshold. XP is added
    // but level up is not done if level is 10 (master).
    addSkillXp(id, outcome = '') {
      const skill = this.skills.find(skill => skill.id === id);
      if (!skill) return;

       // Base xp is a random number between 100 and 300
      let gained_xp = Math.floor(Math.random() * 201) + 100;

      // Multiply base xp based on outcome. Failure still gives good xp
      // to make leveling on lower levels easier.
      const outcome_multipliers = {
        'critical success': 1.5,
        'success': 1.2,
        'partial success': 1.0,
        'failure': 0.9,
        'critical failure': 0.7
      };

      gained_xp *= outcome_multipliers[outcome] ?? 1;

      const xp_required = this.getLevelUpThreshold(skill.level);

      skill.experience += gained_xp

      if (skill.level >= 10) return; // No level up beyond 10

      if (skill.experience >= xp_required) {
        skill.level += 1;
        // Extra xp is carried to next level
        skill.experience = skill.experience - xp_required;
        skill.proficiency = this.levelToProficiency(skill.level);
      }
    },
    // Returns outcome for skill of given level. Table of probabilities
    // for each level and outcome can be found in Project Documentation.
    getSkillOutcome(level) {
      // Roll between 0-100
      const roll = Math.random() * 100;

      // Base crit success chance is 1 %, raised by 1.2 % for each level
      const crit_success = 1 + level * 1.2;

      // Base success chance is 10 %, raised by 4.5 % for each level
      const success = 10 + level * 4.5;

      // Crit failure starts at 20 % on level 0 then lowers 2 %
      // for each level. A minimum 2 % chance is still applied.
      const crit_failure = Math.max(2, 20 - level * 2);

      // Failure starts at 50 % then lowers 4 % each level.
      // A minimum 15 % chance is still applied.
      const failure = Math.max(15, 50 - level * 4);

      // Substract others from 100 to get partial success chance.
      // Value stays around 20 %.
      const partial = 100 - crit_success - success - crit_failure - failure;

      // Calculate which outcome roll belongs to by making higher 
      // rolls mean better outcome.
      let threshold = 0;

      threshold += crit_failure;
      if (roll < threshold) return 'critical failure';

      threshold += failure;
      if (roll < threshold) return 'failure';

      threshold += partial;
      if (roll < threshold) return 'partial success';

      threshold += success;
      if (roll < threshold) return 'success';

      return 'critical success';
    },
    getSkills() {
      return this.skills;
    },
    getSkillsStr() {
      if (this.skills.length === 0) return '';

      let str = '';

      for (const skill of this.skills) {
        str += `- ${skill.name}, ${skill.proficiency}\n`;
      }
      return str.trim();
    },
    removeSkill(id) {
      this.skills = this.skills.filter(skill => skill.id !== id);
    }
  },
  watch: {
    
  },
  computed: {
    // Display skills from newest to oldest
    sortedSkills() {
      return [...this.skills].reverse();
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
      
      <label>Skill Level (0-10, novice to master): 
        <input type="number" v-model="level" min="0" max="10" />
        <span title="Level affects success chance when using skill. Skills gain experience when used, which improves success chance.">
          ⓘ
        </span>
      </label>

      <button @click="addSkill">Add skill</button>
    </div>
  </div>

  <h2>Skills</h2>
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