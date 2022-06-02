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
        <v-row>
            <v-col>
                <div class="display-1">Cities</div>
            </v-col>
        </v-row>
        <v-row dense>
            <v-col
                v-for="city in cities" :key="city"
                class="d-flex child-flex"
                md="2" lg="1"  xs="4">
                <thing-preview :city="city"></thing-preview>
            </v-col>
        </v-row>

        <v-row>
            <v-col>
                <div class="display-1">Counties</div>
            </v-col>
        </v-row>

         <v-row dense>
            <v-col
                v-for="county in counties" :key="county"
                class="d-flex child-flex"
                md="2" lg="1"  xs="4">
                <thing-preview :county="county"></thing-preview>
            </v-col>
        </v-row>

        <v-row>
            <v-col>
                <div class="display-1">States</div>
            </v-col>
        </v-row>

        <v-row dense>
            <v-col
                v-for="state in states" :key="state"
                class="d-flex child-flex"
                md="2" lg="1"  xs="4">
                <thing-preview :state="state"></thing-preview>
            </v-col>
        </v-row>

        <v-row>
            <v-col>
                <div class="display-1">Countries</div>
            </v-col>
        </v-row>

        <v-row dense>
            <v-col
                v-for="country in countries" :key="country"
                class="d-flex child-flex"
                md="2" lg="1"  xs="4">
                <thing-preview :country="country"></thing-preview>
            </v-col>
        </v-row>
    </v-container>
</template>
<script>

    import axios from "axios";
    import ThingPreview from "./ThingPreview";
    export default {

        name: "PlacesView",

        components: {
            ThingPreview
        },

        props: {
        },
        data() {
            return {
                cities: [],
                countries: [],
                counties: [],
                states: []
            };
        },

        mounted() {
            this.loadPlaces();
        },

        computed: {

        },
        watch: {

        },

        methods: {

            loadPlaces() {
                let self = this;
                axios.get("/api/location/countries").then (result => {
                    self.countries = result.data
                });
                axios.get("/api/location/counties").then (result => {
                    self.counties = result.data
                });
                axios.get("/api/location/cities").then (result => {
                    self.cities = result.data
                });
                axios.get("/api/location/states").then (result => {
                    self.states = result.data
                });

            }
        }
    }
</script>