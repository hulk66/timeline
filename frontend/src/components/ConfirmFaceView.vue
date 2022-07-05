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
        </v-img>
        <face-name-selector :loaded="loaded" :closestPerson="face.person" @update="update" :face="face">Correct?</face-name-selector>
    </v-card>
</template>

<script>
    import FaceNameSelector from "./FaceNameSelector"
    export default {
        name: "ConfirmFaceView",

        components: {
            FaceNameSelector
        },

        props: {
            face: Object
        },
        data() {
            return {
                loaded: false
            };
        },


        computed: {
            
            src() {
                return this.face ? this.$basePath + "/api/face/preview/200/" + this.face.id + ".png" : "";
            },
            
        },
        
        mounted() {
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