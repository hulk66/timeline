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
    <v-card>
    <v-tabs v-model="tab">
        <v-tabs-slider></v-tabs-slider>
        <v-tab key="groups">Groups</v-tab>
        <v-tab key="unknown">Unknown</v-tab>
    </v-tabs>
    <v-tabs-items v-model="tab">
        <v-tab-item key="group">
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
                    <person-preview :person="person"></person-preview>
            </v-col>
        </v-row>
    </v-container>

        </v-tab-item>
        <v-tab-item key="unknown">
        <v-container fluid >
        <v-row>
            <v-col>
                <v-card flat>
                    <v-card-title>Unknown</v-card-title>
                    <v-card-text>
                        <div class="text-caption">{{unknownFaces.total}} unnamed Faces</div>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>
        <v-row dense>
        
            <v-col
                v-for="face in unknownFaces.items" :key="face.id" class="d-flex child-flex"
                xs="3" md="2" lg="2" xl="1">
                <face-view @update="updateUnknownFaces" :face="face"></face-view>
            </v-col>
        </v-row>
        <v-row>
            <v-col>
                <v-pagination
                    v-model="page"
                    :length="unknownFaces.pages"
                    
                ></v-pagination>
            </v-col>
        </v-row>
        </v-container>
        </v-tab-item>
    </v-tabs-items>

    </v-card>
</template>
<script>
    import axios from "axios";
    import PersonPreview from "./PersonPreview";
    import { mapState } from 'vuex'
    import FaceView from './FaceView.vue';
    export default {
        name: "PersonsView",

        components: {
            PersonPreview,
            FaceView
        },

        props: {
        },
        data() {
            return {
                tab: 'groups',
                size: 24,
                page: 1
            };
        },

        mounted() {
            this.$store.dispatch("getAllPersons");
            this.$store.dispatch("getKnownPersons");
            this.$store.dispatch("getAllUnknownFaces", {page: this.page, size: this.size});
            this.setFacesSeen();
        },

        watch: {
            page(val) {
                this.$store.dispatch("getAllUnknownFaces", {page: val, size: this.size});

            }, 
            tab(v) {
                if (v == "unknown")
                    this.$store.dispatch("getAllUnknownFaces", {page: this.page, size: this.size});
            }

        },

        computed: {
            ...mapState({
                persons: state => state.person.allPersons,
                knownPersons: state => state.person.knownPersons,
                unknownFaces: state => state.person.unknownFaces
            }),
        },
        methods: {

            setFacesSeen() {
                axios.get("/api/setFacesSeen");
                this.$store.commit("setNewFaces", false);
            },

            updateUnknownFaces() {
                this.$store.dispatch("getAllUnknownFaces", {page: this.page, size: this.size});
                this.$store.dispatch("getAllPersons");
            }
            
        }
    }
</script>