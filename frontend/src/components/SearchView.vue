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
                <v-container fluid>
                    <v-row dense>
                        <v-col>
                            <v-text-field label="Album Name" clearable  v-model="albumName"></v-text-field>
                        </v-col>
                    </v-row>
                </v-container>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="primary" :disabled="!albumName" text @click="saveSmartAlbum">Save Smart Album</v-btn>

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
            albumId: Number
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
                to: "",
                albumName: null,
                id: null
            };
        },

        mounted() {
            this.loadData();
            this.id = this.albumId;
            this.loadSmartAlbum();
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

            loadSmartAlbum() {
                if (this.id)
                    axios.get(`/albums/smartalbum/${this.id}`).then(result => {
                        this.loadSmartAlbumFromData(result.data);
                    })
            },

            loadSmartAlbumFromData(data) {
                this.personId = data.personId;
                this.thing_id = data.thing_id;
                this.camera = data.camera;
                this.city = data.city;
                this.country = data.country;
                this.county = data.county;
                this.rating = data.rating;
                this.to = data.to;
                this.from = data.from;
                this.id = data.id;
                this.albumName = data.name;
            
            },
            saveSmartAlbum() {
                let params = {};
                let config ={ params: params };
                params["person_id"] = this.personId;
                // params["thing_id"] = this.thing_id;
                params["city"] = this.city;
                params["county"] = this.county;
                params["country"] = this.country;
                // params["state"] = this.state;
                params["from"] = this.from;
                params["to"] = this.to;
                params["camera"] = this.camera;
                params["name"] = this.albumName;
                params["rating"] = this.rating;

                axios.get("/albums/create_or_update_smartalbum", config).then(result => {
                    this.loadSmartAlbumFromData(result.data)    
                });
                /*
                axios.get("/albums/create_or_update_smartalbum", {
                    person_id: this.personId,
                    city: this.city,
                    country: this.country,
                    camera: this.camera,
                    from: this.from,
                    to: this.to, 
                    rating: this.rating,
                    name: this.albumName,
                    id: this.albumId
                }).then(result => {
                    this.id = result.data;
                })
                */
            },
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