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
    <v-card :to="{name:'assetWall', query}">
        <v-img :src="src" aspect-ratio="1" gradient="to bottom, rgba(0,0,0,.1), rgba(0,0,0,.5)"
               class="white--text align-end">
            <v-card-text>{{title}}</v-card-text>
        </v-img>
    </v-card>
</template>
<script>


    export default {

        name: "Thumbnail",

        components: {},

        props: {
            src: String,
            title: String,
            query_key: String,
            query_value: String

        },
        data() {
            return {};
        },

        mounted() {
        },

        computed: {
            query() {

                let r = {};
                r[this.query_key] = this.query_value;
                return r;

            }
        },
        watch: {},

        methods: {}
    }
</script>