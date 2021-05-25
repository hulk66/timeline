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
    <div class="d-flex flex-column fill-height pa-2">
        <div >
            <v-text-field ref="nameInput" class="large" v-model="albumName" :readonly="!edit" @keydown.enter="saveName" @click="edit = true"></v-text-field>
            <!--
            <div v-else >{{albumName}}</div>
            -->
        </div>
        <div class="flex-grow-1">
            <photo-wall  
                ref="photoWall"
                :albumId="albumId">
            </photo-wall>
        </div>
    </div>
</template>
<script>
    import axios from 'axios';

    import PhotoWall from './PhotoWall.vue';

    export default {

        name: "AlbumView",

        components: {
            PhotoWall
        },

        props: {
            albumId: Number,
            newAlbum: Boolean,
            
        },
        data() {
            return {
                albumName: "",
                edit: false
            };
        },

        mounted() {
            axios.get(`/albums/info/${this.albumId}`).then((result) => {
                this.albumName = result.data.name
            });
            this.edit = this.newAlbum;
        },

        computed: {
        },
        watch: {
        },

        methods: {
            saveName() {
                axios.get(`/albums/rename/${this.albumId}/${this.albumName}`);
                this.edit = false;
                this.$refs.nameInput.$el.blur();
            }

        }
    }
</script>
<style scoped>
    .large {
        font-size: 36px;
        line-height: 48px;
    }
</style>