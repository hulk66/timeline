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
        <div v-intersect="{handler:onIntersect, options: {threshold: 0.75}}">
        <v-img @click="selectPhoto" 
                :src="thumbSrc" 
                eager
                :class="marked"
                @mouseover="hover = true" 
                @mouseleave="hover = false"
                ref="img"
                >
                <v-fade-transition>
                 <div v-if="hover || marked" class="d-flex bottom-gradient fill-height align-end">
                    
                    <v-rating 
                        class="align-end" 
                        background-color="grey" 
                        color="white" 
                        small 
                        length="5"
                        dense 
                        @input="ratePhoto"
                        @click.native.stop
                        clearable
                        :value="photo.stars">
                    </v-rating>
                </div>
                </v-fade-transition>
        </v-img>
        </div>                    

</template>
<script>


    export default {

        name: "PhotoBrick",

        components: {
        },

        props: {
            photo: Object,
            index: Number,
        },
        data() {
            return {
                hover: false,
                visible: false,
                marked: ""
            };
        },

        mounted() {
        },

        computed: {
            thumbSrc() {
                // return encodeURI("/photos/preview/" + this.targetHeight + "/" + this.photo.path);
                return encodeURI("/photos/preview/400/" + this.photo.path);
            },

        },
        watch: {

        },

        methods: {

            ratePhoto(v) {
                this.$emit("set-rating", this.index, v);
            },
            selectPhoto() {
                this.$emit("select-photo", this.index);
            },

            mark(value) {
                this.marked = value ? "marked" : "";
            },


            getImgElement() {
                return this.$refs.img;
            },
            // eslint-disable-next-line no-unused-vars
            onIntersect(entries, observer) {
                let element = entries[0];
                this.visible = element.isIntersecting
                // console.log("Index " + this.index + " is " + this.visible);
            },

        }
    }
</script>
<style scoped>
    .container {
        position: relative;
        text-align: center;
        padding: 0% ;
    }

    .top-left {
        position: absolute;
        top: 8px;
        left: 16px;
    }

    .top-right {
        position: absolute;
        top: 8px;
        right: 16px;
    }

    .marked {
        border: 5px solid;
        border-color: var(--v-primary-base);
    }

    .bottom-gradient {
        background-image: linear-gradient(to top, rgba(0, 0, 0, 0.75) 0%, transparent 72px);
    }
    
</style>