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
    <v-container fluid>
        <v-row>
            <v-col>
                <div class="display-1">Things</div>
            </v-col>
        </v-row>
        <v-row dense>
            <v-col
                v-for="thing in things" :key="thing.id"
                class="d-flex child-flex"
                md="2" lg="1"  xs="4">
                <thing-preview :thing="thing"></thing-preview>
            </v-col>
        </v-row>
    </v-container>
</template>
<script>

    import axios from "axios";
    import ThingPreview from "./ThingPreview";
    export default {

        name: "ThingsView",

        components: {
            ThingPreview
        },

        props: {
        },
        data() {
            return {
                things: [],
            };
        },

        mounted() {
            this.loadThings();
        },

        computed: {

        },
        watch: {

        },

        methods: {

            src(thing) {
                let self = this;
                axios.get("/api/things/preview_photo" + { thing_id: thing.id }).then (result => {
                    self.photo = result.data
                });
            },
            loadThings() {
                let self = this;
                axios.get("/api/things/all").then (result => {
                    self.things = result.data
                });

            }
        }
    }
</script>