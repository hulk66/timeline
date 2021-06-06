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
    <v-card flat :to="{name:'album', query:{album_id:album.id}}">
        <v-card-text>
        <v-row dense>
            <v-col v-for="p in photos" :key="p.id" class="d-flex child-flex" :cols="cols">
                <v-img :aspect-ratio="ar()" :src="src(p)"></v-img>
            </v-col>
        </v-row>
        </v-card-text>
        <v-card-subtitle class="text-h6" v-text="album.name"></v-card-subtitle>
    </v-card>
</template>
<script>
    import axios from 'axios';
    export default {

        name: "AlbumPreview",

        components: {
            
        },

        props: {
            album: Object
        },
        data() {
            return {
                photos: []
            };
        },

        mounted() {
            axios.get(`/albums/photos/${this.album.id}/4`).then((result) => {
                this.photos = result.data;
            });
        },

        computed: {
            cols() {
                let result = 6;
                if (this.photos.length == 1)
                    result = 12;
                return result;
            }

        },
        watch: {
        },

        methods: {
            src(p) {
                return  encodeURI("/photos/preview/200/" + p.path);
            },

            ar() {
                let r = 1;
                if (this.photos.length == 2) 
                    r = 0.5;
                return r;

            }
        }
    }
</script>