/*
 * Copyright (C) 2021 Tobias Himstedt
 * 
 * 
 * This file is part of Timeline.
 * 
 * Timeline is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * Timeline is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
<template>
  <v-menu
    v-model="menu"
    :close-on-content-click="false"
    :nudge-right="40"
    transition="scale-transition"
    offset-y
    min-width="auto"
  >
    <template v-slot:activator="{ on, attrs }">
      <v-text-field
        v-model="value"
        :label="title"
        prepend-icon="mdi-calendar"
        readonly
        clearable
        v-bind="attrs"
        v-on="on"
      ></v-text-field>
    </template>
    <v-date-picker v-bind:value="value" @input="menu = false"  v-on:input="change"></v-date-picker>
  </v-menu>
</template>
<script> 
export default {
    name: "DatePicker",

    components: {},

    props: {
        value: String,
        title: String
    },
    data() {
        return {
        // date: new Date().toISOString().substr(0, 10),
          menu: false,
        };
    },

    mounted() {
    /*
    if (this.value == null)
        this.value = new Date().toISOString().substr(0, 10);
        */
    },

    computed: {
    
    },
    watch: {},

    methods: {
		change(v) {
			this.$emit("input", v)
		}
	},
};
</script>