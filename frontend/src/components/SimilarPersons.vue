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
    <v-card>
        <v-card-title>Who is this?</v-card-title>
        <v-card-text>
        <v-row>
            <v-col>
                <v-combobox     :search-input.sync="value"
                                :items="knownPersons"
                                item-text="name"
                                item-value="id"
                                v-model="newPerson">
                </v-combobox>

            </v-col>
            <v-col>
                <v-btn @click="submit" :disabled="!value">{{value}}</v-btn>
            </v-col>
        </v-row>

        <v-row style="position: relative">
            <v-col v-for="(face, index) in faces" :key="index" md="2" xs="4" lg="1" >
                <v-card flat @mouseover="showParent(face, $event)" @mouseleave="hideParent()">
                    <v-checkbox v-model="selectedIds" :value="face.id"></v-checkbox>
                    <v-img :src="thumbSrc(face)" height="100%"  ></v-img>
                </v-card>
            </v-col>
            <v-card id="parentPreview" v-if="showDetail" :style="cssProps">
                    <v-img :src="parentUrl"></v-img>
            </v-card>

        </v-row>
        </v-card-text>
    </v-card>
</template>

<script>
    import axios from "axios";
    export default {
        name: "SimilarPersons",

        props: {
        },

        data() {
            return {
                name: "",
                faces: [],
                selectedIds: [],
                personId: this.$route.query.person_id,
                newPerson: null,
                value: "",
                knownPersons: [],
                currentX: Number,
                currentY: Number,
                showDetail: false,
                parentUrl: ""
            };
        },

         computed: {
            cssProps() {
                return {
                    '--current-y': this.currentY + 'px',
                    '--current-x': this.currentX + 'px',
                }
            },
        },

        mounted() {
            this.getFaces();
            this.getKnownPersons();
        },

        watch: {
            faces(val) {
                this.selectedIds = [];
                val.forEach( v => {
                    this.selectedIds.push(v.id)
                })
            },
            newPersonId(val) {
                // eslint-disable-next-line no-console
                console.log(val);

            }
        },
        methods: {
            showParent(face, event) {
                let self = this;
                axios.get("/api/photo/by_face/" + face.id).then( result => {
                    let photo = result.data;
                    self.parentUrl = encodeURI("/photos/preview/200/" + photo.path);
                    self.showDetail = true;
                });
                this.currentX = event.clientX - event.offsetX;
                this.currentY = event.clientY - event.offsetY;

            },
            hideParent() {
                this.showDetail = false;
            },

            getFaces() {
                let self = this;
                axios.get("/api/face/by_person/" + this.personId).then (result => {
                    self.faces = result.data
                });
            },

            getKnownPersons() {
                let self = this;
                axios.get("/api/person/known").then (result => {
                    self.knownPersons = result.data
                });
            },

            thumbSrc(face) {
                if (face)
                    return "/api/face/preview/200/" + face.id + ".png" ;
                else
                    return null;
            },
            submit() {
                let self = this;

                if (! this.newPerson)
                    this.newPerson = this.value;
                axios.post("/api/face/setname", {
                    oldPersonId: this.personId,
                    newPerson: this.newPerson,
                    ids: this.selectedIds,
                }).then(() => {
                    self.$emit('new-person');
                    self.$router.push("/persons");

                }).catch(function (error) {
                    // eslint-disable-next-line no-console
                    console.log(error);
                });
                this.name = "";
            }

        }
    }
</script>

<style scoped>

    #parentPreview {
        position: absolute;
        top: var(--current-y);
        left: var(--current-x);
        width: 200px;

    }
</style>