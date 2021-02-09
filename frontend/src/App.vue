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
    <v-app id="timline">
        <v-navigation-drawer
                v-model="drawer"
                app
                clipped
                expand-on-hover
                mini-variant>
            <v-list>
                <v-list-item-group>
                    <v-list-item :to="{name:'photoWall'}">
                        <v-list-item-action>
                            <v-icon>mdi-view-dashboard</v-icon>
                        </v-list-item-action>
                        <v-list-item-content>
                            <v-list-item-title>All</v-list-item-title>
                        </v-list-item-content>
                    </v-list-item>

                    <v-list-item to="/persons">
                        <v-list-item-action>
                            <v-badge :content="newFaces" dot :value="newFaces">
                                <v-icon>mdi-face</v-icon>
                            </v-badge>
                        </v-list-item-action>
                        <v-list-item-content>
                            <v-list-item-title>People</v-list-item-title>
                        </v-list-item-content>
                    </v-list-item>

                    <v-list-item to="/things">
                        <v-list-item-action>
                            <v-icon>mdi-lightbulb</v-icon>
                        </v-list-item-action>
                        <v-list-item-content>
                            <v-list-item-title>Things</v-list-item-title>
                        </v-list-item-content>
                    </v-list-item>
                    <v-list-item to="/places">
                        <v-list-item-action>
                            <v-icon>mdi-map-marker</v-icon>
                        </v-list-item-action>
                        <v-list-item-content>
                            <v-list-item-title>Places</v-list-item-title>
                        </v-list-item-content>
                    </v-list-item>
                </v-list-item-group>
            </v-list>
        </v-navigation-drawer>

        <v-app-bar
                app
                clipped-left dense>
            <v-app-bar-nav-icon @click.stop="drawer = !drawer"/>
            <v-toolbar-title>Timeline - Photo Organizer</v-toolbar-title>


            <v-spacer></v-spacer>
                  <v-menu left bottom>

                      <template v-slot:activator="{ on, attrs }">
                        <v-btn icon v-bind="attrs" v-on="on">
                            <v-icon>mdi-dots-vertical</v-icon>
                        </v-btn>
                      </template>

                      <v-list subheader width="300">
                          <v-list-item>
                              <v-list-item-content>
                                  <v-switch v-model="darkmode" label="Dark Mode"></v-switch>
                              </v-list-item-content>
                          </v-list-item>

                          <v-list-item>
                               <v-list-item-content>
                                    <v-list-item-title>Processed Photos</v-list-item-title>
                              </v-list-item-content>
                              <v-list-item-action>{{totalPhotos}}</v-list-item-action>
                          </v-list-item>

                          <v-list-item>
                               <v-list-item-content>
                                    <v-list-item-title>Identified Faces</v-list-item-title>
                              </v-list-item-content>
                              <v-list-item-action>{{totalFaces}}</v-list-item-action>
                          </v-list-item>

                          <v-list-item>
                               <v-list-item-content>
                                    <v-list-item-title>Identified Things</v-list-item-title>
                              </v-list-item-content>
                              <v-list-item-action>{{totalThings}}</v-list-item-action>
                          </v-list-item>

                          <v-list-item>
                              <v-list-item-content>
                                    <v-dialog
                                          v-model="about"
                                          persistent
                                          max-width="400"
                                        >
                                          <template v-slot:activator="{ on, attrs }">
                                            <v-btn
                                              color="primary" text 
                                              v-bind="attrs"
                                              v-on="on">
                                              About
                                            </v-btn>
                                          </template>
                                          <v-card>
                                            <v-card-title class="headline">
                                              Timeline - Photo Organizer
                                            </v-card-title>
                                            <v-card-text>
                                                <v-list dense>
                                                    <v-list-item>
                                                        <v-list-item-icon>
                                                            <v-icon>mdi-copyright</v-icon>
                                                        </v-list-item-icon>
                                                        <v-list-item-content>Tobias Himstedt</v-list-item-content>
                                                    </v-list-item>
                                                    <v-list-item>
                                                        <v-list-item-icon>
                                                            <v-icon>mdi-at</v-icon>
                                                        </v-list-item-icon>
                                                        <v-list-item-content>
                                                            <a href="mailto://himstedt@gmail.com">himstedt@gmail.com</a>
                                                            </v-list-item-content>
                                                    </v-list-item>

                                                </v-list>

                                            </v-card-text>
                                            <v-card-actions>
                                              <v-spacer></v-spacer>
                                              <v-btn
                                                color="primary"
                                                text
                                                @click="about = false"
                                              >
                                                OK
                                              </v-btn>
                                            </v-card-actions>
                                          </v-card>
                                        </v-dialog>
                              </v-list-item-content>
                          </v-list-item>
                          <v-list-group  @click.stop>
                            <template v-slot:activator>
                                <v-list-item-content>
                                    <v-list-item-title>Queued Jobs</v-list-item-title>
                                </v-list-item-content>
                            </template>

                          <!--
                          <v-subheader>Queued Jobs</v-subheader>
                          -->
                          <v-list-item>
                              <v-list-item-content>
                                    <v-list-item-title>Processing</v-list-item-title>
                              </v-list-item-content>
                              <v-list-item-action>{{process_count}}</v-list-item-action>
                          </v-list-item>
                          <v-list-item>
                              <v-list-item-content>
                                  <v-list-item-title>Face detection</v-list-item-title>
                              </v-list-item-content>
                              <v-list-item-action v-text="faces_count"></v-list-item-action>
                          </v-list-item>
                          <v-list-item>
                              <v-list-item-content>
                              <v-list-item-title>Object detection</v-list-item-title>
                              </v-list-item-content>
                              <v-list-item-action v-text="things_count"></v-list-item-action>

                          </v-list-item>
                          <v-list-item>
                              <v-list-item-content>
                              <v-list-item-title>Address Detection</v-list-item-title>
                              </v-list-item-content>
                              <v-list-item-action v-text="geo_count"></v-list-item-action>
                          </v-list-item>
                          <v-list-item>
                              <v-list-item-content>
                              <v-list-item-title>Quality Assessment</v-list-item-title>
                              </v-list-item-content>
                              <v-list-item-action v-text="iq_count"></v-list-item-action>
                          </v-list-item>
                                                  </v-list-group>

                            <v-list-group   @click.stop>
                            <template v-slot:activator>
                                <v-list-item-content>
                                    <v-list-item-title>Currently Processing</v-list-item-title>
                                </v-list-item-content>
                            </template>
                            <!--
                          <v-subheader>Currently processing</v-subheader>
                          -->
                          <v-list-item v-for="(job, key, index) in active" :key="index">
                              <v-list-item-content>
                              <v-list-item-title v-text="key"></v-list-item-title>
                              <v-list-item-subtitle v-for="p in job" v-text="p" :key="p"></v-list-item-subtitle>
                              </v-list-item-content>

                          </v-list-item>
                            </v-list-group>
                      </v-list>

                  </v-menu>

        </v-app-bar>

        <v-main>
            <router-view :key="$route.fullPath">></router-view>
        </v-main>
    </v-app>
</template>

<script>
    import axios from "axios";
    import { mapState } from 'vuex'

    export default {
        props: {
            source: String,
        },

        data() {
            return {
                darkmode: false,
                selectedItem: {type:'all'},
                faces: [],
                drawer: null,
                updateInProgress: false,
                active: Object,
                faces_count: 0,
                things_count: 0,
                process_count: 0,
                geo_count: 0,
                inStatusCheck: false,
                about: false,
                totalFaces: 0,
                totalThings: 0,
                totalPhotos: 0,
                iq_count: 0
            };
        },


        computed: {
            ...mapState({
                knownPersons: state => state.person.knownPersons,
                newFaces: state => state.person.newFaces
            }),
        },
        watch: {

            darkmode(val) {
                this.$vuetify.theme.dark = val
            },

            selectedItem(val) {

                if (val.type == 'unknown')
                    axios.get("/api/cluster/faces/" + val.value).then((result) => {
                        this.faces = result.data
                    }).catch((error) => {
                        // eslint-disable-next-line
                        console.error(error);
                });
            },

        },

        mounted() {
            this.checkNewFaces();
            setInterval( this.getStatusJobs, 5000 ); // 5 seconds
            setInterval( this.checkNewFaces, 1000*60*5 ); // 5 Minutes

        },
        methods: {
            person(i) {
                return this.knownPersons[i]
            },
            p(p, i) {
                return p + i.toString();
            },

            checkNewFaces() {
                let self = this;
                axios.get("/api/checkNewFaces").then ( result => {
                    self.$store.commit("setNewFaces", result.data);
                    // self.newFaces = result.data;
                });

            },
            getStatusJobs() {
                if (this.inStatusCheck)
                    return;
                this.inStatusCheck = true
                axios.get("/inspect/status", {params: {timestamp:new Date().getTime()}}).then((result) => {
                    if (result.data.active)
                        this.active = result.data.active;

                    this.geo_count = result.data.geo;
                    this.faces_count = result.data.faces;
                    this.things_count = result.data.things;
                    this.process_count = result.data.process;
                    this.iq_count = result.data.iq;
                    this.inStatusCheck = false,
                    this.totalFaces = result.data.totalFaces;
                    this.totalThings = result.data.totalThings;
                    this.totalPhotos = result.data.totalPhotos;
                })

            },

        }
    }
</script>