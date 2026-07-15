function handler(event) {
  var request = event.request;
  var uri = request.uri;
  var lastSegment = uri.substring(uri.lastIndexOf("/") + 1);

  if (uri.endsWith("/") || !lastSegment.includes(".")) {
    request.uri = "/index.html";
  }

  return request;
}
