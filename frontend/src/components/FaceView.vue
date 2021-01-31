<template>
    <v-card flat>
        <v-img :src="src"></v-img>
        <v-card-subtitle>Closest {{closestPerson.name}} with Distance {{distance}}</v-card-subtitle>
    </v-card>
</template>

<script>

    export default {
        name: "FacePreview",

        components: {
        },

        props: {
            face: Object
        },
        data() {
            return {
                closestPerson: Object,
                distance: 0.0
            };
        },


        computed: {
            src() {
                return "/api/face/preview/200/" + this.face.id + ".png";
            },

        },
        mounted() {
            this.$store.dispatch("getClosestPerson", this.face).then(result => {
                this.closestPerson = result.person;
                this.distance = result.distance;
            });

        },

        watch: {

        },

        methods: {


        }
    }
</script>