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
    <v-card flat>
        <v-card-title>Currently imported and sorted</v-card-title>
        <v-card-text>
        <vue-justified-layout
                :items="assets"
                v-slot="{item}"
                :options="{
                    targetRowHeight: 200,
                    boxSpacing: 5,
                    containerPadding:5}">
                    <v-img :src="thumbSrc(item)" eager></v-img>
        </vue-justified-layout>
</v-card-text>
    </v-card>
</template>
<script>
    import axios from 'axios';

    export default {

        name: "ImportView",

        components: {   
        },

        props: {
            
        },
        data() {
            return {
                assets: []
            };
        },

        mounted() {
            axios.get(process.env.BASE_URL + `api/asset/importing`).then((result) => {
                this.assets = result.data;
            });
        },

        computed: {
        },
        watch: {
        },

        methods: {
            thumbSrc(asset) {
                return encodeURI(process.env.BASE_URL + "assets/preview/400/high_res/" + asset.path);
            }
        }
    }
</script>