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
    <v-tabs v-model="tab" @change="changeTab">
        <v-tabs-slider></v-tabs-slider>
        <v-tab key="known">Known ({{knownPersons.length}})</v-tab>
        <v-tab key="confirm">To be confirmed ({{facesToConfirm.total}})</v-tab>
        <v-tab key="unknown">Unknown ({{unknownFaces.total}})</v-tab>
        <v-tab key="recent">Recent faces({{recentFaces.total}})</v-tab>
    </v-tabs>
    <v-tabs-items v-model="tab">
        <v-tab-item key="known">
            <v-container fluid >
                <v-row>
                    <v-col class="d-flex child-flex" cols="2">
                        <v-card flat>
                            <v-card-title>Persons</v-card-title>
                            <v-card-text>
                                <div class="text-caption">{{persons.total}} Persons, {{knownPersons.length}} known</div>
                            </v-card-text>
                        </v-card>
                    </v-col>
                    <v-col>
                        <filter-box :knownPersons="knownPersons" @applyFilters="applyFiltersKnown" :showPersonFilter="true" :showConfidenceFilter="false"></filter-box>
                    </v-col>
                </v-row>

                <v-row dense>
                    <v-col
                        v-for="person in persons.items" :key="person.id" class="d-flex child-flex"
                        xs="3" md="2" lg="1" xl="1">
                        <person-preview :person="person"></person-preview>
                    </v-col>
                    <div class="persons-loading query-loading-spinner" visibility='hidden'>
                        <v-progress-circular color="primary" indeterminate></v-progress-circular>
                    </div>
                </v-row>
                <v-row>
                    <v-col>
                        <v-pagination
                            v-model="knownPersonTab.page"
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
                    <face-view @update="updateFacesToConfirm" :face="face" :selectorText="'Correct?'" :showAssetStamp="true" :showDistance="true" :showFaceConfidence="true"></face-view>
                </v-col>
                <div class="confirmFaces-loading query-loading-spinner" visibility='hidden'>
                    <v-progress-circular color="primary" indeterminate></v-progress-circular>
                </div>
            </v-row>
            <v-row>
                <v-col>
                    <v-pagination
                        v-model="confirmFacesTab.page"
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
                            <div class="text-caption">{{unknownFaces.total}} unnamed Faces</div>
                            <v-btn @click="ignoreAllOnPage()" block text color="primary" 
                                @mouseover="hoverIgnoreAll = true"
                                @mouseleave="hoverIgnoreAll = false">
                                Ignore All On Page
                                <v-icon right>mdi-close</v-icon>
                            </v-btn>
                            <v-btn @click="changeTab(2);" block text color="primary" >
                                Refresh
                                <v-icon right>mdi-refresh</v-icon>
                            </v-btn>
                        </v-card-text>
                    </v-card>
                </v-col>
                <v-col>
                    <v-container class="d-flex child-flex col recentFaces" id="recentFaces">
                        <v-row dence>
                            <v-col
                                v-for="face in mostRecentFaces.items" :key="face.id" class="d-flex child-flex"
                                xs="3" md="2" lg="1" xl="1">
                                <face-view @update="updateUnknownFaces" :face="face"  :showFaceConfidence="true"
                                    :showAssetStamp="false" :showDistance="false" :miniVersion="true"></face-view>
                            </v-col>
                        </v-row>
                        <div class="mostRecentFaces-loading query-loading-spinner" visibility='hidden'>
                            <v-progress-circular color="primary" indeterminate></v-progress-circular>
                        </div>
                    </v-container>
                </v-col>
            </v-row>
            <v-row dense id="unknownFacesList">
                <v-col :class="{ 'on-hover': hoverIgnoreAll }"
                    v-for="element in unknownFaces.items" :key="element.id" class="d-flex child-flex unknownFace"
                    xs="3" md="2" lg="2" xl="1">
                    <face-view @update="updateUnknownFaces" :face="element" :showAssetStamp="true" :showDistance="true"
                                :showFaceConfidence="true"
                                :selectorText="'Whos is this'" ></face-view>
                </v-col>
                <div class="unknownFaces-loading query-loading-spinner" visibility='hidden'>
                    <v-progress-circular color="primary" indeterminate></v-progress-circular>
                </div>
            </v-row>
            <v-row>
                <v-col>
                    <v-pagination
                        v-model="unknownFacesTab.page"
                        :length="unknownFaces.pages"
                        
                    ></v-pagination>
                </v-col>
            </v-row>
            </v-container>
        </v-tab-item>
        <v-tab-item key="recent">
            <v-container fluid >
            <v-row>
                <v-col>
                    <v-col class="d-flex child-flex" cols="2">
                        <v-card flat>
                            <v-card-title>Recently processed faces</v-card-title>
                            <v-card-text>
                                <div class="text-caption">{{recentFaces.total}} faces were processed</div>
                            </v-card-text>
                            </v-card>
                    </v-col>
                    <v-col>
                        <filter-box :knownPersons="knownPersons" @applyFilters="applyFiltersRecent" :showPersonFilter="true" :showConfidenceFilter="true"></filter-box>
                    </v-col>
                </v-col>
            </v-row>
            <v-row>
                <v-col
                    v-for="face in recentFaces.items" :key="face.id" class="d-flex child-flex"
                    xs="3" md="2" lg="2" xl="1">
                    <face-view @update="updateRecentFaces" :face="face" :showFaceConfidence="true"
                        :showAssetStamp="false" :showDistance="false" :miniVersion="true"></face-view>
                </v-col>
                <div class="recentFaces-loading query-loading-spinner" visibility='hidden'>
                    <v-progress-circular color="primary" indeterminate></v-progress-circular>
                </div>
            </v-row>
            <v-row>
                <v-col>
                    <v-pagination
                        v-model="recentFacesTab.page"
                        :length="recentFaces.pages"
                        
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
    import FilterBox from './FilterBox.vue';
    export default {
        name: "PersonsView",

        components: {
            PersonPreview,
            FaceView,
            FilterBox
        },

        props: {
        },
        data() {
            return {
                tab: 'groups',
                hoverIgnoreAll: false,
                recentMostFacesQuery: false,
                knownPersonTab: {
                    size: 24,
                    page: 1,
                    filters: {
                        person: null,
                        switchNone: true,
                        switchMayBe: true,
                        switchSafe: true,
                        switchVerySafe: true,
                        switchConfirmed: true,
                    }
                },
                unknownFacesTab: {
                    size: 24,
                    page: 1,
                    filters: {
                        person: null,
                        switchNone: true,
                        switchMayBe: true,
                        switchSafe: true,
                        switchVerySafe: true,
                        switchConfirmed: true,
                    }
                },
                recentFacesTab: {
                    size: 24,
                    page: 1,
                    filters: {
                        person: null,
                        switchNone: true,
                        switchMayBe: true,
                        switchSafe: true,
                        switchVerySafe: true,
                        switchConfirmed: true,
                    }
                },
                confirmFacesTab: {
                    size: 24,
                    page: 1,
                    filters: {
                        person: null,
                        switchNone: true,
                        switchMayBe: true,
                        switchSafe: true,
                        switchVerySafe: true,
                        switchConfirmed: true,
                    }
                },
            };
        },

        mounted() {
            this.$store.dispatch("getAllPersons");
            this.$store.dispatch("getPersons", {
                    page: this.knownPersonTab.page,
                    size: this.knownPersonTab.size,
                    filters: this.knownPersonTab.filters,
                });

            this.$store.dispatch("getKnownPersons");
            this.setFacesSeen();
        },

        watch: {
            'knownPersonTab.page': function (val){
                this.$store.dispatch("getPersons", {
                    page: val,
                    size: this.knownPersonTab.size,
                    filters: this.knownPersonTab.filters
                });
            },
            'unknownFacesTab.page': function (val){
                this.$store.dispatch("getAllUnknownFaces", {page: val, size: this.unknownFacesTab.size, filters: this.unknownFacesTab.filters});
            },
            'confirmFacesTab.page': function (val){
                this.$store.dispatch("getFacesToConfirm", {page: val, size: this.confirmFacesTab.size});
            }, 
            'recentFacesTab.page': function (val){
                this.$store.dispatch("getRecentFaces", {page: val, size: this.recentFacesTab.size, filters: this.recentFacesTab.filters});
            }, 

            tab(v) {
                if (v == "unknown")
                    this.$store.dispatch("getAllUnknownFaces", {page: this.unknownFacesTab.page, size: this.unknownFacesTab.size, filters: this.unknownFacesTab.filters});
            }

        },

        computed: {
            ...mapState({
                persons: state => state.person.persons,
                knownPersons: state => state.person.knownPersons,
                unknownFaces: state => state.person.unknownFaces,
                recentFaces: state => state.person.recentFaces,
                mostRecentFaces: state => state.person.mostRecentFaces,
                facesToConfirm: state => state.person.facesToConfirm,
            }),
        },
        methods: {

            setFacesSeen() {
                axios.get("/api/setFacesSeen");
                this.$store.commit("setNewFaces", false);
            },

            updateUnknownFaces() {
                this.$store.dispatch("getAllUnknownFaces", {page: this.unknownFacesTab.page, size: this.unknownFacesTab.size, filters: this.unknownFacesTab.filters});
                this.$store.dispatch("getAllPersons");
                this.$store.dispatch("getPersons", {
                    page: this.knownPersonTab.page,
                    size: this.knownPersonTab.size,
                    filters: this.knownPersonTab.filters,
                });
                this.$store.dispatch("getMostRecentFaces", {size: this.recentFacesTab.size});
            },

            updateFacesToConfirm() {
                this.$store.dispatch("getFacesToConfirm", {page: this.confirmFacesTab.page, size: this.confirmFacesTab.size});
            },
            
            updateRecentFaces() {
                this.$store.dispatch("getRecentFaces", {page: this.recentFacesTab.page, size: this.recentFacesTab.size, filters: this.recentFacesTab.filters});
            },
            
            ignoreAllOnPage() {
                console.log("Ignoring all the faces: ", this.unknownFaces);
                let facesToIgnore = []
                this.unknownFaces.items.forEach( faceInfo => {
                    facesToIgnore.push(faceInfo.id);
                });
                this.$store.dispatch("ignoreFace", facesToIgnore).then(result => {
                    console.log("Ignored the faces result: "+result);
                    this.$store.dispatch("getPersons", {
                        page: this.knownPersonTab.page,
                        size: this.knownPersonTab.size,
                        filters: this.knownPersonTab.filters,
                    });

                    this.$store.dispatch("getMostRecentFaces", {size: this.recentFacesTab.size});
                    this.$store.dispatch("getAllUnknownFaces", {page: this.unknownFacesTab.page, size: this.unknownFacesTab.size, filters: this.unknownFacesTab.filters});
                    this.$emit("update");
                });
            },

            changeTab(tabIndex) {
                console.log("Changing tab to ", tabIndex);
                window.axios_api_cache.clear_cache();
                switch(tabIndex) {
                    case 0: { // "known"
                        this.$store.dispatch("getAllPersons");
                        this.$store.dispatch("getPersons", {
                            page: this.knownPersonTab.page,
                            size: this.knownPersonTab.size,
                            filters: this.knownPersonTab.filters,
                        });
                        this.$store.dispatch("getKnownPersons");
                        break;                        
                    }
                    case 1: { // "confirm"
                        this.$store.dispatch("getFacesToConfirm", {page: this.confirmFacesTab.page, size: this.confirmFacesTab.size});
                        break;                        
                    }
                    case 2: { // "unknown"
                        this.$store.dispatch("getAllUnknownFaces", {page: this.unknownFacesTab.page, size: this.unknownFacesTab.size, filters: this.unknownFacesTab.filters});
                        this.$store.dispatch("getMostRecentFaces", {size: this.recentFacesTab.size});
                        break;                        
                    }
                    case 3: { //"recent"
                        this.$store.dispatch("getRecentFaces", {page: 1, size: this.recentFacesTab.size, filters: this.recentFacesTab.filters});
                        break;                        
                    }
                }
                this.setFacesSeen();
            },

            applyFiltersKnown(filters) {
                this.knownPersonTab.filters = filters;
                this.changeTab(0);
            },

            applyFiltersUnknown(filters) {
                this.unknownFacesTab.filters = filters;
                this.changeTab(2);
            },

            applyFiltersRecent(filters) {
                this.recentFacesTab.filters = filters;
                this.changeTab(3);
            },

        }
    }
</script>

<style scoped>
.recentFaces {
    border: 1px solid #D0D0D0;
    border-radius: 10px;
    min-height: 264px;
}
.filtersBox {
    border: 1px solid #D0D0D0;
    border-radius: 10px;
}
.on-hover > div{
    background-color: #D0D0D0 !important;
}
.query-loading-spinner {
    position: absolute;
}
</style>