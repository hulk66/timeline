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
        <v-img :src="src" height="200px" contain @load="loaded=true" @click="clickPhoto" >
            <template v-slot:placeholder>
                <v-row
                class="fill-height ma-0"
                align="center"
                justify="center">
                    <v-progress-circular color="primary" indeterminate></v-progress-circular>
                </v-row>
            </template>
            <v-container fluid class="assetStamp">
                {{assetStamp}}
            </v-container>
        </v-img>
        <face-name-selector :loaded="loaded" :closestPerson="closestPerson" :distance="distance" @update="update" :face="face">Whos is this</face-name-selector>
        <!--
        <v-card-subtitle>Closest {{closestPerson.name}} with Distance {{distance}}</v-card-subtitle>
        -->
        <v-dialog
            v-model="photoFullscreen"
            fullscreen hide-overlay
            @keydown="keyboardActionDialog($event)"
            ref="viewerDialog">
            <image-viewer :photo="currentPhotoAsset.photo" ref="viewer"
                            :faceToFocus="currentPhotoAsset.face"
                            :nextPhoto="null"
                            v-if="photoFullscreen && currentPhotoAsset"
                            :prevPhoto="null"
                            :direction="imageViewerDirection"
                            @close="closeViewer"
                            @left="navigate(-1)"
                            @right="navigate(1)">
            </image-viewer>
        </v-dialog>

    </v-card>
</template>

<script>
    import FaceNameSelector from "./FaceNameSelector";
    import ImageViewer from "./ImageViewer";

    export default {
        name: "FaceView",

        components: {
            FaceNameSelector,
            ImageViewer
        },

        props: {
            element: Object 
        },
        data() {
            return {
                photoFullscreen: false,
                currentPhotoAsset: null,
                prevPhoto: null,
                nextPhoto: null,
                imageViewerDirection: 0,
                /*
                closestPerson: Object,
                distance: 0.0,
                face: Object,
                */
                loaded: false
            };
        },


        computed: {
            
            src() {
                return this.element ? this.$basePath + "/api/face/preview/200/" + this.face.id + ".png" : "";
            },
            face() {
                return this.element ? this.element.face : null;
            },

            closestPerson() {
                return this.element ? this.element.person: null;
            },

            distance() {
                return this.element ? this.element.distance : null;
            },

            assetStamp() {
                return (this.element && this.element.face && this.element.face.asset_stamp) ? this.element.face.asset_stamp.split(" ")[0] : "";
            }
            
        },
        
        mounted() {
            /*    
            this.$store.dispatch("getClosestPerson", this.face).then(result => {
                this.closestPerson = result.person;
                this.distance = result.distance;
            });
            */
        },
        
        watch: {

        },

        methods: {
            update() {
                // there is a better way of doing this with event bus
                this.$emit("update")
            },

            closeViewer() {
                this.photoFullscreen = false;
                this.currentPhotoAsset = null;
            },
            clickPhoto() {
                console.log("Click on the face ", this.element.face)
                this.photoFullscreen = true;
                this.imageViewerDirection = 0;
                this.currentPhotoAsset = this.element;
                this.prevPhoto = null;
                this.nextPhoto = null;
            },
            keyboardActionDialog(event) {
                // are these values somewhere defined as constants?
                if (event.code == "ArrowLeft")
                    this.navigate(-1);
                else if (event.code == "ArrowRight")
                    this.navigate(1);
                else if (event.code == "Escape")
                    this.closeViewer();
            },
            navigate(dir) {
                console.log("Navigation clicked but not supported", dir)
            }
        }
    }
</script>

<style scoped>
    .assetStamp {
        background-color: transparent; 
        padding: 3px; 
        text-shadow: 1px 1px #D0D0D0; 
        float:right; 
        text-align: center; 
        vertical-align: bottom; 
        bottom: -5px;
        position: absolute;
    }
</style>