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
    <div class="d-flex flex-column fill-height">
        <div class="ma-2">
            <v-text-field 
                ref="nameInput"
                label="Album Name"
                :rules="[rules.required]"
                v-model="albumName" 
                :readonly="!edit" 
                @focus="select($event)"
                @keydown.enter="saveName" 
                @click="edit = true"></v-text-field>
            <!--
            <div v-else >{{albumName}}</div>
            -->
        </div>
        <div class="flex-grow-1">
            <photo-wall  
                ref="photoWall"
                :showPhotoCount="false"
                :selectionAllowed="true"
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
                edit: false,
                rules: {
                    required: value => !!value || 'Required.',
                },
            };
        },

        mounted() {
            this.edit = this.newAlbum;
            axios.get(`/albums/info/${this.albumId}`).then((result) => {
                this.albumName = result.data.name
                this.$store.commit("setSelectedAlbum", result.data)
                if (this.edit) {
                    this.$nextTick(() => {
                        this.$refs.nameInput.focus();
                        this.$refs.nameInput.$el.querySelector('input').select();
                    });
                }
            });
        },

        computed: {
        },
        watch: {
        },

        // eslint-disable-next-line no-unused-vars
        beforeRouteLeave(to, from, next) {
            this.$store.commit("setSelectedAlbum", null)
            next();
        },
        methods: {
            select(event) {
                event.target.select();
            },
            saveName() {
                axios.get(`/albums/rename/${this.albumId}/${this.albumName}`);
                this.edit = false;
                this.$refs.nameInput.blur();
            }

        }
    }
</script>
<style scoped>
    .v-text-field {
        font-size: 32px;
        line-height: 48px;
    }
    
    /* what a mess to find this out!! */
    .v-text-field >>> input {
        max-height: unset;
    }
</style>