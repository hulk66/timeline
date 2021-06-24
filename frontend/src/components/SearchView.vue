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
    <v-container fluid class="fill-height">
        <v-row no-gutters class="fill-height">
            <v-col cols=2>
                <v-card flat>
                    <v-container fluid>
                    <v-row dense>
                        <v-col>
                            <date-picker :value="from" @input="changeFrom" title="From"></date-picker>
                        </v-col>
                    </v-row>
                    <v-row dense>
                        <v-col>
                            <date-picker :value="to" @input="changeTo" title="To"></date-picker>
                        </v-col>
                    </v-row>
                    <v-row dense>
                        <v-col>
                            Rating
                            <v-rating clearable v-model="rating"></v-rating>
                        </v-col>
                    </v-row>
                    <v-row dense>
                        <v-col>
                            <v-select clearable label="Country" :items="countries" v-model="country"></v-select>
                        </v-col>
                    </v-row>
                    <v-row dense>
                        <v-col>
                            <v-select clearable label="City" :items="cities" v-model="city"></v-select>
                        </v-col>
                    </v-row>
                    <v-row dense>
                        <v-col>
                            <v-select clearable label="Person" :items="knownPersons" item-value="id" item-text="name" v-model="personId"></v-select>
                        </v-col>
                    </v-row>
                    <v-row dense>
                        <v-col>
                            <v-select clearable label="Camera Make" :items="cameras" v-model="camera"></v-select>
                        </v-col>
                    </v-row>
                </v-container>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="primary" text @click="$refs.photoWall.loadAllSections()">Search</v-btn>
                </v-card-actions>
                </v-card>
            </v-col>
            <v-col>
                <photo-wall
                    ref="photoWall"
                    :city="city"
                    :country="country"
                    :camera="camera"
                    :personId="personId"
                    :from="from"
                    :to="to"
                    :rating="rating">
                </photo-wall>

            </v-col>
        </v-row>
    </v-container>
</template>
<script>

    import DatePicker from './DatePicker.vue';
    import { mapState } from 'vuex'
    import axios from "axios";
    import PhotoWall from './PhotoWall.vue';

    export default {

        name: "SearchView",

        components: {
            DatePicker,
            PhotoWall
        },

        props: {
        },
        data() {
            return {
                /*
                criterias: [],
                criteria: "",
                criteriaList: ["Date Range", "Rating", "Camera Make", "Country", "City", "Person"],
                */
                cities: [],
                countries: [],
                cameras: [],
                camera: "",
                country: "",
                city: "",
                personId: null,
                rating: 0,
                from: "", 
                to: ""
            };
        },

        mounted() {
            this.loadData();
        },

        computed: {
            ...mapState({
                knownPersons: state => state.person.knownPersons,
            })
        },
        watch: {
        },

         // eslint-disable-next-line no-unused-vars
        beforeRouteLeave(to, from, next) {
            this.$store.commit("emptySelectedPhotos");
            next();
        },
        
        methods: {
            changeFrom(val) {
                this.from = val;
                this.to = val;
            },

            changeTo(val) {
                this.to = val;
            },
            loadData() {
                axios.get("/api/location/countries").then (result => {
                    this.countries = result.data
                });
                axios.get("/api/location/cities").then (result => {
                    this.cities = result.data
                });
                
                axios.get("/api/exif/camera_makes").then (result => {
                    this.cameras = result.data
                });
                

            },
            addCriteria() {
                let crit = null;
                switch (this.criteria) {
                    case "Date Range":
                        crit = {
                            type:"date", from: null, to: null
                        }
                        break;
                    case "Rating":
                        crit = {
                            type:"rating", rating: 0
                        }
                        break;
                    case "Camera Make":
                        crit = {
                            type:"camera", make: ""
                        }
                        break;
                    case "Country":
                        crit = {
                            type:"country", name: ""
                        }
                        break;
                    case "City":
                        crit = {
                            type:"city", name: ""
                        }
                        break;
                    case "Person":
                        crit = {
                            type:"person", name: ""
                        }
                        break;

                }
                let c = this.criteria;
                this.criteriaList = this.criteriaList.filter(function(value){ 
                    return value != c;
                });
                this.criterias.push(crit);

            }

        }
    }
</script>