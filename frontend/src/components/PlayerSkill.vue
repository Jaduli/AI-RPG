<script>
export default {
  data() {
    return {
      collapse: true
    }
  },
  props: {
    skill: {
      type: Object,
      required: true
    }
  },
  emits: ['remove']
}
</script>

<template>
    <div class="skill">
      <h3>{{ skill.name }} <span class="skill-level">({{ skill.proficiency }})</span></h3>

      <button @click="collapse = !collapse">{{ collapse ? 'Edit' : 'Collapse' }}</button>
      <div v-if="!collapse">          
        <h4>Name</h4>
        <input type="text" v-model="skill.name" maxlength="25" />

        <button class="btn btn-danger" @click="$emit('remove')">Forget skill</button>
      </div>
    </div>
</template>

<style>
.skill {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.skill > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.skill textarea {
  min-height: 50px;
}
.skill h4 {
  margin: 3px 0 3px;
}
.skill button {
  margin-bottom: 10px;
}
.skill-level {
  font-size: 0.7em;
  color: #aa3bff;
  font-weight: normal;
}
</style>