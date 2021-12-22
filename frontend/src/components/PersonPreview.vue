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
    <v-card flat link>
            <v-img link v-if="src" :src="src"  width="100%"  contain  @click="clickFace">
                <template v-slot:placeholder>
                    <v-row
                        class="fill-height ma-0"
                        align="center"
                        justify="center">
                    <v-progress-circular
                    indeterminate
                    color="grey lighten-5"
                    ></v-progress-circular>
                  </v-row>
                </template>
            </v-img>
        <div v-if="personObject.confirmed">
            <v-menu :close-on-content-click="false" v-model="showRename" offset-y>
                <template v-slot:activator="{ on, attrs }">
                    <div class="text-center">
                    <v-btn small color="primary" text v-bind="attrs" v-on="on">
                    {{personObject.name}}
                    </v-btn>
                    </div>
                </template>
                <v-card>
                    <v-card-title>Rename</v-card-title>
                    <v-card-text>
                        <v-text-field v-model="faceName" label="New Name"></v-text-field> 
                    </v-card-text>
                <v-card-actions>
                        <v-btn color="warning" icon @click="forgetPerson"><v-icon>mdi-update</v-icon></v-btn>
                        <v-spacer></v-spacer>
                        <v-btn color="primary" icon @click="showRename=false"><v-icon>mdi-close</v-icon></v-btn>
                        <v-btn color="primary" icon @click="rename"><v-icon>mdi-check</v-icon></v-btn>
                    </v-card-actions>
                </v-card>
            </v-menu>

        </div>
        <div v-else>
            <v-menu :close-on-content-click="false" v-model="showSelection" offset-y>
                <template v-slot:activator="{ on, attrs }">
                    <div class="text-center">
                    <v-btn small text color="primary" v-bind="attrs" v-on="on">
                        Who is this?
                    </v-btn>
                    </div>
                </template>
                <v-card>
                    <v-card-title>Select existing or create new</v-card-title>
                    <v-card-text>
                        <v-combobox :search-input.sync="faceName"
                                                        :items="knownPersons"
                                                        item-text="name"
                                                        item-value="id"                                                
                                                        v-model="newPerson">                                                                                                            
                        </v-combobox>                        
                </v-card-text>
                <v-card-actions>
                    <v-btn color="error" icon @click="ignoreUnknowPerson"><v-icon>mdi-delete</v-icon></v-btn>
                    <v-spacer></v-spacer>
                        <v-btn color="primary" icon @click="showSelection=false"><v-icon>mdi-close</v-icon></v-btn>
                        <v-btn color="primary" :disabled="!faceName" icon @click="assignOrRenamePerson"><v-icon>mdi-check</v-icon></v-btn>
                    </v-card-actions>
                </v-card>
            </v-menu>
        </div>
                    
    </v-card>

</template>
<script>
    import axios from "axios";
    import { mapState } from 'vuex'
    export default {
        name: "PersonPreview",

        components: {
        },

        props: {
            person: Object
        },
        data() {
            return {
                face: null,
                src: null,
                dialog: false,
                edit: false,
                editId: Number,
                faceName: "",
                newPerson: null,
                showRename: false,
                showSelection: false,
                personObject: Object,
                closestPerson: Object
            };
        },


        computed: {
            ...mapState({
                knownPersons: state => state.person.knownPersons
            })
        },
        mounted() {
            this.personObject = this.person;
            if (this.personObject) {
                axios.get("/api/face/data/by_person/" + this.person.id).then (result => {
                    this.face = result.data;
                    this.src = "/api/face/preview/200/" + this.face.id + ".png";

                });

            }
        },

        watch: {

            showSelection(v) {
                if (v)
                    this.$store.dispatch("getClosestPerson", this.face).then(result => {
                        this.newPerson = result.person;
                    });
            }
        },

        methods: {
            forgetPerson() {
                 this.$store.dispatch("forgetPerson", this.personObject).then((result) => {
                        this.$store.commit("setAllPersons", result)
                    }); 
                this.showSelection = false;

            },
            ignoreUnknowPerson() {
                 this.$store.dispatch("ignoreUnknownPerson", this.personObject).then((result) => {
                        this.$store.commit("setAllPersons", result)
                    });
                this.showSelection = false;
            },
            assignOrRenamePerson() {
                if (! this.newPerson || this.newPerson instanceof String || this.faceName != this.newPerson.name) {
                    // The unknown person will receive a name
                    this.rename();

                } else {
                    // The faces will be assigend to another person
                    this.$store.dispatch("mergePerson", {src_person:this.personObject, target_person:this.newPerson}).then(() => {
                        this.$store.dispatch("getKnownPersons");
                        this.$store.dispatch("getAllPersons");
                    });
                    this.showSelection = false;

                }

            },

            rename() {
                this.$store.dispatch("renamePerson", {person:this.person, name:this.faceName}).then(result => {
                    this.personObject = result;
                    this.$store.dispatch("getKnownPersons");
                });
                this.showRename = false;
            },
            clickFace() {
                if (this.person.confirmed)
                    this.$router.push({name:'assetWall', query:{ person_id:this.person.id}});
                else
                    this.$router.push( {name:'similarPersons', query:{ person_id:this.person.id}});
            },
            to(person) {
                if (person.confirmed)
                    return {name:'assetWall', query:{ person_id:person.id}};
                else {
                    return {name:'similarPersons', query:{ person_id:person.id}}

                }
            }
        }
    }
</script>