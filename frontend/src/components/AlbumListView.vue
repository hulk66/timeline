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
        <v-row>
            <v-col
                v-for="album in albums" :key="album.id"
                class="d-flex child-flex"
                xs="3" md="2" lg="2" xl="2">
                    <album-preview :album="album"></album-preview>
                </v-col>
        </v-row>
    </v-container>
</template>
<script>
    import axios from 'axios';
    import AlbumPreview from './AlbumPreview'
    export default {

        name: "AlbumListView",

        components: {   
            AlbumPreview
        },

        props: {
            
        },
        data() {
            return {
                albums: []
            };
        },

        mounted() {
            axios.get(`/albums/all`).then((result) => {
                this.albums = result.data;
            });
        },

        computed: {
        },
        watch: {
        },

        methods: {

        }
    }
</script>