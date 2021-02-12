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
    <v-card flat>
        <v-list>

            <v-list-item  v-if="closestPerson">
                <v-list-item-content>
                    <v-list-item-subtitle>
                            <v-btn @click="confirm()" block text color="primary">
                                {{closestPerson.name}}
                                 <v-icon right>mdi-check</v-icon>
                            </v-btn>
                    </v-list-item-subtitle>
                </v-list-item-content>
            </v-list-item>
            <v-list-item>
                <v-list-item-content>
                    <v-list-item-subtitle>
                    <v-menu :close-on-content-click="false" v-model="showSelection" offset-y>
                        <template v-slot:activator="{ on, attrs }">
                            <v-btn block text color="secondary" v-bind="attrs" v-on="on">
                                Other
                            </v-btn>
                        </template>

                        <v-card>
                            <v-card-title>Select existing or create new</v-card-title>
                            <v-card-text>
                                <v-combobox :search-input.sync="name"
                                            :items="knownPersons"
                                            item-text="name"
                                            item-value="id"                                                
                                            v-model="selectedPerson">                                                                                                            
                                </v-combobox>            
                        </v-card-text>
                        <v-card-actions>
                            <v-btn color="error" icon @click="ignoreFace()"><v-icon>mdi-delete</v-icon></v-btn>
                            <v-spacer></v-spacer>
                                <v-btn color="primary" icon @click="close()"><v-icon>mdi-close</v-icon></v-btn>
                                <v-btn color="primary" :disabled="!name" icon @click="assignFaceToPerson()"><v-icon>mdi-check</v-icon></v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-menu>

                    </v-list-item-subtitle>
                </v-list-item-content>

            </v-list-item>
        </v-list>
    </v-card>
</template>
<script>
    import { mapState } from 'vuex'

    export default {
        
        name: "FaceNameSelector",
        props: {
            face: Object,
            loaded: Boolean,
            closestPerson: Object
        },

        data() {
            return {
                name: "",
                selectedPerson: null,
                showSelection: false,
                distance: 0.0,
                // closestPerson: null

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
        computed: {
            ...mapState({
                knownPersons: state => state.person.knownPersons
            })
        },
        watch: {},
        methods: {
            close() {
                this.showSelection = false;
            },
            ignoreFace() {
                this.$store.dispatch("ignoreFace", this.face).then(() => {
                    this.$emit("update");
                    this.close();

                })

            },

            assignFaceToPerson() {
                // The faces will be assigend to another person
                this.$store.dispatch("assignFaceToPerson", {person:this.selectedPerson, name:this.name, faceId:this.face.id}).then(() => {
                    this.$store.dispatch("getKnownPersons");
                    this.$emit("update")
                    this.close();
                });

            },

            confirm() {
                this.selectedPerson = this.closestPerson;
                this.name = this.closestPerson.name;
                this.assignFaceToPerson();
            }
        }
    }
</script>