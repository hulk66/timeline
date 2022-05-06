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
    <div>
    <v-container fluid >
        <v-row no-gutters >
            <v-col 
                v-for="album in albums" :key="album.id"
                class="d-flex child-flex"
                cols="6" md="4" lg="2" xl="1">
                    <album-preview :album="album"></album-preview>
                </v-col>
        </v-row>
    </v-container>
    <!--
    <v-container fluid >
        <v-row no-gutters >
            <v-col 
                v-for="album in smartAlbums" :key="album.id"
                class="d-flex child-flex"
                cols="6" md="4" lg="2" xl="1">
                    <album-preview smart :album="album"></album-preview>
                </v-col>
        </v-row>
    </v-container>
    -->
    </div>
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
                albums: [],
            };
        },

        mounted() {
            axios.get(process.env.BASE_URL + `albums/all`).then((result) => {
                this.albums = result.data;
            });

            this.$store.commit("setSelectedAlbum", null);
        },

        computed: {
        },
        watch: {
        },

        methods: {

        }
    }
</script>