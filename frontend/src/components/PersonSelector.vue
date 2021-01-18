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
    <v-combobox     :search-input.sync="personName"
                    :items="knownPersons"
                    item-text="name"
                    item-value="id"
                    v-model="selectedPerson">
    </v-combobox>
</template>
<script>
    import axios from "axios";
    export default {
        
        name: "PersonSelector",
        props: {
            selectedPerson: Object,
        },

        data() {
            return {
                knownPersons: [],
                personName: ""
            }
        },
        mounted() {
            this.getKnownPersons();
        },
        computed: {},
        watch: {},
        methodes: {
            getKnownPersons() {
                let self = this;
                axios.get("/api/person/known").then (result => {
                    self.knownPersons = result.data
                });
            },
        }
    }
</script>