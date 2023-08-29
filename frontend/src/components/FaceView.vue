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
        <v-img :src="src" :height="tileHeight" contain @load="loaded=true" @click="clickPhoto" >
            <template v-slot:placeholder>
                <v-row
                class="fill-height ma-0"
                align="center"
                justify="center">
                    <v-progress-circular color="primary" indeterminate></v-progress-circular>
                </v-row>
            </template>
            <v-container fluid class="assetStamp" v-if="showAssetStamp">
                {{assetStamp}}
            </v-container>
            <v-container fluid :class="faceConfidence.class" v-if="showFaceConfidence">
                <v-icon :color="faceConfidence.color" >{{faceConfidence.icon}}</v-icon>
            </v-container>
        </v-img>
        <face-name-selector :loaded="loaded" :closestPerson="face.person" @update="update" :face="face" :showDistance="showDistance" v-if="!miniVersion">{{selectorTextValue}}</face-name-selector>
        <mini-face-name-selector :loaded="loaded" :closestPerson="face.person" @update="update" :face="face"  v-if="miniVersion" :currentName="selectorTextValue">{{selectorTextValue}}</mini-face-name-selector>
        <!--
        <v-card-subtitle>Closest {{face.person.name}} with Distance {{distance}}</v-card-subtitle>
        -->
        <v-dialog
            v-model="photoFullscreen"
            fullscreen hide-overlay
            @keydown="keyboardActionDialog($event)"
            ref="viewerDialog">
            <image-viewer :photo="currentPhotoAsset.photo" ref="viewer"
                            :faceToFocus="currentPhotoAsset"
                            :nextPhoto="null"
                            v-if="photoFullscreen && currentPhotoAsset.photo"
                            :prevPhoto="null"
                            :direction="imageViewerDirection"
                            @close="closeViewer"
                            @set-rating="setRating"
                            @left="navigate(-1)"
                            @right="navigate(1)">
            </image-viewer>
        </v-dialog>

    </v-card>
</template>

<script>
    import FaceNameSelector from "./FaceNameSelector";
    import MiniFaceNameSelector from "./MiniFaceNameSelector";
    import ImageViewer from "./ImageViewer";

    export default {
        name: "FaceView",

        components: {
            FaceNameSelector,
            MiniFaceNameSelector,
            ImageViewer
        },

        props: {
            face: Object,
            showAssetStamp: Boolean,
            showFaceConfidence: Boolean,
            showDistance: Boolean,
            selectorText: String,
            miniVersion: Boolean
        },

        data() {
            return {
                photoFullscreen: false,
                currentPhotoAsset: null,
                prevPhoto: null,
                nextPhoto: null,
                imageViewerDirection: 0,
                loaded: false
            };
        },


        computed: {
            
            src() {
                return this.face ? this.$basePath + "/api/face/preview/200/" + this.face.id + ".png" : "";
            },

            tileHeight() {
                return this.miniVersion ? "100px" : "200px";
            },

            assetStamp() {
                return (this.face && this.face.asset_stamp) ? this.face.asset_stamp.split(" ")[0] : "";
            },

            faceConfidence() {
                switch(this.face.confidence_level) {
                    case 0: { // "None"
                        return {
                            class: "faceConfidence",
                            icon: "mdi-eye-circle",
                            color: "warning"
                        };
                    }
                    case 1: { // "MayBe"
                        return {
                            class: "faceConfidence fc_none",
                            icon: "mdi-help-circle",
                            color: "info"
                        };
                    }
                    case 2: { // "Safe"
                        return {
                            class: "faceConfidence",
                            icon: "mdi-leaf-circle",
                            color: "info"
                        };
                    }
                    case 3: { // "Very Safe"
                        return {
                            class: "faceConfidence",
                            icon: "mdi-star-circle",
                            color: "info"
                        };
                    }
                    case 4: { // "Confirmed"
                        return {
                            class: "faceConfidence",
                            icon: "mdi-check-circle",
                            color: "success"
                        };
                    }
                    default: {
                        if (this.face.confidence_level === null) {
                            return {
                                class: "faceConfidence",
                                icon: "mdi-circle-outline",
                                color: "grey-lighten-2"
                            };
                        } else {
                            return {
                                class: "faceConfidence",
                                icon: "mdi-alert",
                                color: "error"
                            };
                        }
                    }
                }
            },

            selectorTextValue() {
                if (this.selectorText) {
                    return this.selectorText;
                }
                if (this.face.distance == -1 && this.face.person) {
                    return this.face.person.name;
                }
                return "-----";
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
                console.log("Click on the face ", this.face)
                this.photoFullscreen = true;
                this.imageViewerDirection = 0;
                this.currentPhotoAsset = this.face;
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
            },
            setRating(value) {
                this.$store.dispatch("setRating", {photo: this.currentPhotoAsset.photo, stars: value}).then( result => {
                    this.$store.commit("currentPhotoAsset.photo", result);
                });
            },

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
    .faceConfidence {
        background-color: transparent; 
        padding: 3px; 
        text-shadow: 1px 1px #D0D0D0; 
        float:right; 
        text-align: right; 
        vertical-align: bottom; 
        bottom: -5px;
        position: absolute;
    }

</style>