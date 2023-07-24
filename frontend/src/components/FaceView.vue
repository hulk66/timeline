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
        <v-img :src="src" height="200px" contain @load="loaded=true">
            <template v-slot:placeholder>
                <v-row
                class="fill-height ma-0"
                align="center"
                justify="center">
                    <v-progress-circular color="primary" indeterminate></v-progress-circular>
                </v-row>
            </template>
            <v-container fluid style="background-color: transparent; padding: 3px; text-shadow: 1px 1px #D0D0D0; float:right; text-align: center; vertical-align: bottom; bottom: 0px;position: absolute;">
                {{assetStamp}}
            </v-container>
        </v-img>
        <face-name-selector :loaded="loaded" :closestPerson="closestPerson" @update="update" :face="face">Whos is this</face-name-selector>
        <!--
        <v-card-subtitle>Closest {{closestPerson.name}} with Distance {{distance}}</v-card-subtitle>
        -->
    </v-card>
</template>

<script>
    import FaceNameSelector from "./FaceNameSelector"

    export default {
        name: "FaceView",

        components: {
            FaceNameSelector
        },

        props: {
            element: Object
        },
        data() {
            return {
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
            }

        }
    }
</script>