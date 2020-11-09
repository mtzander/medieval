function setupReset() {
  $('[id=reset]').on('click', function() {
    $('[name=year_start').val(null)
    $('[name=year_end').val(null)
    $('[name=source').val(null)
    $('[name=place').val(null)
    $('[name=artist').val(null)
    $('[name=institution]').val('')
    $('[name=medium]').val('')
    $('[name=country').prop( "checked", false )
    $('[name=costume').prop( "checked", false )
    $('[name=gender').prop( "checked", false )
    $('[name=art]').val('')
  })
}

function setupTagSearchField(initial_values) {
  var input = document.querySelector('textarea[id=tags]')
  window.addEventListener('load', onLoad)
  input.addEventListener('change', onChange)
  function onLoad() {
    $('[name=tag]').val(JSON.parse($('[id=tags]').val() || '[]').map(function(e) { return e.id }))
  }
  function onChange(e){
    $('[name=tag]').val(JSON.parse(e.target.value || '[]').map(function(e) { return  e.id }))
  }
  var tagify = new Tagify(input, {
    editTags: false,
    enforceWhitelist: true,
    whitelist: initial_values
  })
  tagify.on('input', onInput)
  $('[id=reset]').on('click', function() {
    tagify.removeAllTags()
    $('[name=tag]').val([])
  })
  function onInput(e) {
    if(e.detail.value.length === 0) {
      return
    }
    $.ajax({
      method: "GET",
      url: "/tags/suggest/"+e.detail.value
    }).done(function( result ) {
      tagify.settings.whitelist = result
      tagify.dropdown.show.call(tagify, e.detail.value)
    })
  }
}

function setupTagEditor(id, mode) {
  var input = document.querySelector('textarea[name=tags]')
  var tagify = new Tagify(input, {
    editTags: false,
    hooks: {
      beforeRemoveTag: function(tags) {
        $('#remove-confirmation').modal({})
        return new Promise((resolve, reject) => {
          $('#confirm-removal').on('click', function(z) {
            $.ajax({
              method: "POST",
              url: "/tags/remove",
              data: { name: tags[0].data.value, id: id, mode: mode }
            })
            resolve()
          })
          $('#dismiss-removal').on('click', function(z) {
            reject()
          })
        })
      }
    }
  })
  tagify.on('add', onAddTag).on('input', onInput).on('click', onClick)
  function onAddTag(e) {
    $.ajax({
      method: "POST",
      url: "/tags/add",
      data: { name: e.detail.data.value, id: id, mode: mode }
    }).done(function(result) {
      tagify.replaceTag(tagify.getTagElms()[e.detail.index],{value: e.detail.data.value, id: result})
    })
  }
  function onInput(e) {
    if(e.detail.value.length === 0) {
      return
    }
    $.ajax({
      method: "GET",
      url: "/tags/suggest/"+e.detail.value
    }).done(function( result ) {
      tagify.settings.whitelist = result
      tagify.dropdown.show.call(tagify, e.detail.value)
    })
  }
  function onClick(e) {
    window.location.href = "/search?tag="+e.detail.data.id+"#results"
  }
}

function setupDetailMap(title, lat, long) {
  var map = new google.maps.Map(document.getElementById("map"), {
    zoom: 5,
    disableDefaultUI: true,
    mapTypeId: google.maps.MapTypeId.HYBRID,
    center: {lat: lat, lng: long}
  })
  new google.maps.Marker({
    position: {lat: lat, lng: long},
    map: map,
    title: title,
  })
}

function setupFullMap(data) {
  var map = new google.maps.Map(document.getElementById("map"), {
    zoom: 5,
    disableDefaultUI: true,
    mapTypeId: google.maps.MapTypeId.HYBRID,
    center: {lat: 50.1176, lng: 4.70093}
  })
  function addLink(marker, id) {
    marker.addListener('click', function() {
      window.location.href = '/' + id
    })
  }
  for (i = 0; i < data.length; i++) {
    var m = new google.maps.Marker({
      position: {lat: data[i].lat, lng: data[i].lng},
      map: map,
      title: data[i].name
    })
    addLink(m, data[i].id)
  }
}
