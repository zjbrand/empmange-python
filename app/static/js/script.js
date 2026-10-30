/**
 * 
 */

function getTime() {

    const date = new Date()

    var year = date.getFullYear()
    var month = date.getMonth() + 1
    var day = date.getDate()
    var week = date.getDay()
    var h = date.getHours()
    var m = date.getMinutes()
    var s = date.getSeconds()

    let arr = ['日', '月', '火', '水', '木', '金', '土']

    month = month < 10 ? '0' + month : month
    day = day < 10 ? '0' + day : day

    h = h < 10 ? '0' + h : h
    m = m < 10 ? '0' + m : m
    s = s < 10 ? '0' + s : s

    var nowTime = year + '年' + month + '月' + day + '日' + '&nbsp&nbsp' +arr[week] + '曜日' + 
      '&nbsp&nbsp&nbsp&nbsp&nbsp' + h + '時' + m + '分' + s + '秒'

    return nowTime
  }
