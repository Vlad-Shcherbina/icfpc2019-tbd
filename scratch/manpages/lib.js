const puppeteer = require('puppeteer')

init = async () => {
	const browser = await puppeteer.launch({ headless: true })
	const page = await browser.newPage()
	await page.setViewport({ width: 1920, height: 1080 })
	return [browser, page]
}
exports.init = init

run = async (p, m, s) => {
  const np = p.waitForNavigation({timeout: 60000})
  
  await p.goto('file:///' + __dirname + '/icfpcontest2019.github.io/solution_checker/index.html')

  await p.waitForSelector('#submit_task')
  await p.waitForSelector('#submit_solution')
  await p.waitForSelector('#execute_solution')

  const f1input = await p.$('#submit_task')
  await f1input.uploadFile(m)
  const f2input = await p.$('#submit_solution')
  await f2input.uploadFile(s)
  await p.click('#execute_solution')
  await p.waitFor(35)
  await p.click('#execute_solution')
  await p.waitFor(10)
  var result = await p.evaluate(() => document.querySelector('#output').textContent)
  while (result.startsWith('Pre-processing') ) {
    await p.waitFor(20)
    result = await p.evaluate(() => document.querySelector('#output').textContent)
  }

  await np

  return [result, p]
}
exports.run = run

normalizeResult = (x) => {
  if (x.startsWith('Success')) {
    return 'Success ' + x.match(/\d+/)
  }
}
exports.normalizeResult = normalizeResult
