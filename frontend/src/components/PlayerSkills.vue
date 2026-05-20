<script>
import Skill from './PlayerSkill.vue';

export default {
  data() {
    return {
      collapse: false,
      name: '',
      level: 0,
      proficiency: '', // = level as a word, e.g. 'novice'
      experience: 0,
      skills: []
    }
  },
  components: { Skill },
  methods: {
    // Add skill with id, name, content, experience, and level
    addSkill() {
      const level = this.level;
      const experience = this.level * 1000;
      const proficiency = this.levelToProficiency(level)

      const payload = {
        id: Date.now(),
        name: this.name,
        content: this.content,
        level,
        proficiency,
        experience
      };
      this.skills.push(payload);
      this.name = '';
      this.content = '';
      this.level = 0;
      this.proficiency = '';
      this.experience = 0;
    },
    // Formats a level from 0 to 10 to a matching word.
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
    // Examples: 0->1 = 400, 1->2 = 600, 5->6 = 1400.
    // With this formula, it takes about (level + 2)
    // actions to level up.
    // It should be noted that success gives higher xp gain,
    // making it easier to get xp on a higher levels.
    getLevelUpThreshold(level) {
      return 400 + (level * 200);
    },
    // Adds xp to skill based on action outcome. Levels up 
    // skill if xp is over level up threshold.
    // Returns true if level up, false if not.
    addSkillXp(id, outcome = '') {
      const skill = this.skills.find(skill => skill.id === id);
      if (!skill) return;

      let gained_xp = 200; // Base xp

      // Multiply xp based on outcome. Failure still gives good xp
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

      if (skill.experience >= xp_required) {
        skill.level += 1;
        skill.experience = Math.max(0, skill.experience - xp_required);
        skill.proficiency = this.levelToProficiency(skill.level);
      }
    },
    // Returns outcome for skill of given level.
    getSkillOutcome(level) {
      // Roll between 0-100
      const roll = Math.random() * 100;

      // Each level adds 1.2 % crit success chance
      const crit_success = 1 + level * 1.2;

      // Each level adds 4.5 % success chance
      const success = 10 + level * 4.5;

      // Crit failure starts at 20 % on level 0 then lowers 2 %
      // for each level. A minimum 2 % chance is still applied.
      const crit_failure = Math.max(2, 20 - level * 2);

      // Failure starts at then lowers 4 % each level.
      // A minimum 15 % chance is still applied.
      const failure = Math.max(15, 50 - level * 4);

      // Substract others from 100 to get partial succes chance
      const partial = 100 - crit_success - success - crit_failure - failure;

      // Find which outcome roll belongs to
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
    useSkill(id) {
      const skill = this.skills.find(skill => skill.id === id);
      const outcome = this.getSkillOutcome(skill.level);

      return outcome;
    },
    getSkills() {
      return this.skills;
    },
    getSkillsStr() {
      if (this.skills.length === 0) return '';

      let str = '[Player Skills & Proficiency]\n';

      for (const skill of this.skills) {
        const proficiency = this.levelToProficiency(skill.level);

        str += `- ${skill.name}, ${proficiency}\n`;
      }
      return str;
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
        <span title="Level affects success chance. Skills gain experience when used. Leveling up takes about (level + 2) actions.">
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