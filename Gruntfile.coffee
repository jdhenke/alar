module.exports = (grunt) ->

  grunt.initConfig

    pkg: grunt.file.readJSON "package.json"

    coffee:
      compileSource:
        files:
          "public/js/main.js": ["coffee/**/*.coffee"]

    watch:
      coffee:
        "files": ["coffee/**/*.coffee"]
        "tasks": ["coffee"]

  grunt.loadNpmTasks 'grunt-contrib-coffee'
  grunt.loadNpmTasks 'grunt-contrib-watch'

  grunt.registerTask "default", ["coffee"]
