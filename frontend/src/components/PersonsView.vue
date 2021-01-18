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
    <v-container fluid >
        <v-row>
            <v-col>
                <v-card flat>
                    <v-card-title>Persons</v-card-title>
                    <v-card-text>
                        <div class="text-caption">{{persons.length}} Persons, {{knownPersons.length}} known</div>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>
        <v-row dense>
        
            <v-col
                v-for="person in persons" :key="person.id"
                class="d-flex child-flex"
                xs="3" md="2" lg="1" xl="1">
                    <face-preview :person="person"></face-preview>
            </v-col>
        </v-row>
    </v-container>
</template>
<script>
    import axios from "axios";
    import FacePreview from "./FacePreview";
    import { mapState } from 'vuex'
    export default {
        name: "PersonsView",

        components: {
            FacePreview
        },

        props: {
        },
        data() {
            return {
            };
        },

        mounted() {
            this.$store.dispatch("getAllPersons");
            this.$store.dispatch("getKnownPersons");
            this.setFacesSeen();
        },

        watch: {
        },

        computed: {
            ...mapState({
                persons: state => state.person.allPersons,
                knownPersons: state => state.person.knownPersons
            })
        },
        methods: {

    
            setFacesSeen() {
                axios.get("/api/setFacesSeen");
                this.$store.commit("setNewFaces", false);
            },
            
        }
    }
</script>