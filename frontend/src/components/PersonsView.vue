/*
 * Copyright (C) 2021, 2022 Tobias Himstedt
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
    <v-container fluid>
    <v-card flat>
    <v-tabs v-model="tab">
        <v-tabs-slider></v-tabs-slider>
        <v-tab key="known">Known ({{knownPersons.length}})</v-tab>
        <v-tab key="confirm">To be confirmed ({{facesToConfirm.total}})</v-tab>
        <v-tab key="unknown">Unknown ({{unknownFaces.total}})</v-tab>
    </v-tabs>
    <v-tabs-items v-model="tab">
        <v-tab-item key="known">
            <v-container fluid >
                <v-row>
                    <v-col>
                        <v-card flat>
                            <v-card-title>Persons</v-card-title>
                            <v-card-text>
                                <div class="text-caption">{{persons.total}} Persons, {{knownPersons.length}} known</div>
                            </v-card-text>
                        </v-card>
                    </v-col>
                </v-row>
            <v-row dense>
                <v-col
                    v-for="person in persons.items" :key="person.id" class="d-flex child-flex"
                    xs="3" md="2" lg="1" xl="1">
                    <person-preview :person="person"></person-preview>
                </v-col>
            </v-row>
            <v-row>
                <v-col>
                    <v-pagination
                        v-model="pageConfirm"
                        :length="persons.pages"
                    ></v-pagination>
                </v-col>
            </v-row>                
            </v-container>
        </v-tab-item>

        <v-tab-item key="confirm">
            <v-container fluid >
            <v-row>
                <v-col>
                    <v-card flat>
                        <v-card-title>To confirm</v-card-title>
                        <v-card-text>
                            <div class="text-caption">{{facesToConfirm.total}} faces to confirm</div>
                        </v-card-text>
                    </v-card>
                </v-col>
            </v-row>
            <v-row>
                <v-col
                    v-for="face in facesToConfirm.items" :key="face.id" class="d-flex child-flex"
                    xs="3" md="2" lg="2" xl="1">
                    <confirm-face-view @update="updateFacesToConfirm" :face="face"></confirm-face-view>
                </v-col>
            </v-row>
            <v-row>
                <v-col>
                    <v-pagination
                        v-model="pageConfirm"
                        :length="facesToConfirm.pages"
                        
                    ></v-pagination>
                </v-col>
            </v-row>
            </v-container>
        </v-tab-item>
        <v-tab-item key="unknown">
            <v-container fluid >
            <v-row>
                <v-col class="d-flex child-flex" cols="2">
                    <v-card flat>
                        <v-card-title>Unknown faces</v-card-title>
                        <v-card-text>
                            <div class="text-caption">{{unknownFaces.total}} unnamed Faces 1</div>
                            <v-btn @click="ignoreAllOnPage()" block text color="primary">
                                Ignore All On Page
                                 <v-icon right>mdi-close</v-icon>
                            </v-btn>
                        </v-card-text>
                    </v-card>
                </v-col>
                <v-col>
                    <v-container class="d-flex child-flex col recentFaces">
                        <v-row dence>
                            <v-col
                                v-for="faceInfo in recentFaces.items" :key="faceInfo.face.id" class="d-flex child-flex"
                                xs="3" md="2" lg="1" xl="1">
                                <mini-face-view @update="updateUnknownFaces" :element="faceInfo"></mini-face-view>
                            </v-col>
                        </v-row>
                    </v-container>
                </v-col>
            </v-row>
            <v-row dense>
            
                <v-col
                    v-for="element in unknownFaces.items" :key="element.face.id" class="d-flex child-flex"
                    xs="3" md="2" lg="2" xl="1">
                    <face-view @update="updateUnknownFaces" :element="element"></face-view>
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
    </v-container>
</template>
<script>
    import axios from "axios";
    import PersonPreview from "./PersonPreview";
    import { mapState } from 'vuex'
    import FaceView from './FaceView.vue';
    import ConfirmFaceView from './ConfirmFaceView'
    import MiniFaceView from './MiniFaceView.vue';
    export default {
        name: "PersonsView",

        components: {
            PersonPreview,
            FaceView,
            ConfirmFaceView,
            MiniFaceView
        },

        props: {
        },
        data() {
            return {
                tab: 'groups',
                size: 24,
                page: 1,
                sizeConfirm: 24,
                pageConfirm: 1
            };
        },

        mounted() {
            this.$store.dispatch("getAllPersons");
            this.$store.dispatch("getPersons", {page: this.page, size: this.size});
            this.$store.dispatch("getKnownPersons");
            this.$store.dispatch("getAllUnknownFaces", {page: this.page, size: this.size});
            this.$store.dispatch("getFacesToConfirm", {page: this.page, size: this.size});
            this.$store.dispatch("getRecentFaces", {page: 1, size: this.size});
            this.setFacesSeen();
        },

        watch: {
            page(val) {
                this.$store.dispatch("getAllUnknownFaces", {page: val, size: this.size});
            }, 
            pageConfirm(val) {
                this.$store.dispatch("getFacesToConfirm", {page: val, size: this.sizeConfirm});
            }, 

            tab(v) {
                if (v == "unknown")
                    this.$store.dispatch("getAllUnknownFaces", {page: this.page, size: this.size});
            }

        },

        computed: {
            ...mapState({
                persons: state => state.person.persons,
                knownPersons: state => state.person.knownPersons,
                unknownFaces: state => state.person.unknownFaces,
                recentFaces: state => state.person.recentFaces,
                facesToConfirm: state => state.person.facesToConfirm
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
                this.$store.dispatch("getPersons", {page: this.page, size: this.size});
                this.$store.dispatch("getRecentFaces", {page: 1, size: this.size});
            },

            updateFacesToConfirm() {
                this.$store.dispatch("getFacesToConfirm", {page: this.pageConfirm, size: this.sizeConfirm});
            },
            
            ignoreAllOnPage() {
                console.log("Ignoring all the faces: ", this.unknownFaces);
                this.unknownFaces.items.forEach( faceInfo => {
                    this.$store.dispatch("ignoreFace", faceInfo.face);
                });
                this.$store.dispatch("getPersons", {page: this.page, size: this.size});
                this.$store.dispatch("getRecentFaces", {page: 1, size: this.size});
                this.$emit("update");
                this.close();
            }
        }
    }
</script>

<style scoped>
.recentFaces {
    border: 1px solid #D0D0D0;
    border-radius: 10px;
}
</style>