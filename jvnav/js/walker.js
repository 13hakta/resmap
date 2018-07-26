var JList, JBread, JDesc, JTree;

class JavaTree {
	constructor() {
		this.reset();
	}

	toString() {
		return this.data.length;
	}

	reset() {
		this.data = [];
	}

	get(index) {
		return (index <= this.data.length)? this.data[index] : null;
	}

	getClass(index) {
		var curIndex = index;
		var path = [], el;

		while (curIndex != 0) {
			el = this.get(curIndex);
			path.unshift(el[0]);
			curIndex = el[3];
		}

		return path.join('.');
	}

	getPath(index) {
		var curIndex = index;
		var path = [], el;

		while (curIndex != 0) {
			el = this.get(curIndex);
			path.unshift('<li class="breadcrumb-item" data-index="' + curIndex + '">' + el[0] + '</li>');
			curIndex = el[3];
		}

		path.unshift('<li class="breadcrumb-item" data-index="0">' + this.data[0][0] + '</li>');

		return path.join('');
	}

	load(data) {
		this.reset();

		var rec, lines = data.split("\n");

		for (var i in lines) {
			if (lines[i] == "") continue;

			rec = lines[i].split(';');
			rec[1] = (rec[1] == '1')? true : false;
			rec[2] = rec[2].split(',');
			rec[2] = rec[2].map(Number);
			this.data.push(rec);
		}

		// Root has no parent
		this.data[0].push(0);

		// Fill parent
		for (var i in this.data) {
			rec = this.data[i];
			if (rec[1]) {
				for (var j in rec[2])
					this.data[rec[2][j]].push(Number(i));
			}
		}
	}
}

function render(root) {
	var item = JTree.get(root);
	var folders = '', files = '';

	if (item == null) return;

	var index, content = '<div class="card"><div class="card-body">';

	JList.empty();

	if (root > 0)
		JBread.html('<nav aria-label="breadcrumb"><ol class="breadcrumb">' + JTree.getPath(root) + '</ol></nav>');
	else
		JBread.empty();

	for (var key in item[2]) {
		index = item[2][key];
		subitem = JTree.get(index);

		if (subitem[1])
			folders += '<div class="item cat" data-index="' + index + '">' + subitem[0] + '</div>';
		else
			files += '<div class="item file" data-index="' + index + '">' + subitem[0] + ' <span class="badge badge-secondary">' + subitem[2].length + '</span></div>';
	}

	content += folders + files;
	content += '</div></div>';

	JList.html(content);

	JBread.find('.breadcrumb-item').click(function(o){
		render(o.target.dataset.index);
	});

	JList.find('.cat').click(function(o){
		render(o.target.dataset.index);
	});

	JList.find('.file').click(function(o){
		var id = o.target.dataset.index,
		content = '<div class="card"><div class="card-header">';
		content += JTree.getClass(id);
		content += '</div><div class="card-body">';

		var item = JTree.get(id);
		item = item[2];

		for (var i in item) {
			var subitem = JTree.getClass(item[i]);
			content += '<span class="cldesc" data-index="' + item[i] + '">' + subitem + '</a><br/>';
		}

		content += '</div></div>';
		JDesc.html(content);
		JDesc.find('.cldesc').click(function(o) {
			var item = JTree.get(o.target.dataset.index);
			render(item[3]);
			JList.find('.file[data-index=' + o.target.dataset.index + ']').click();
		});
	});
}

function renderTop() {
	render(0);
}

function reload() {
	$.get('js/usemap.txt', {}, function(data) {
		JTree.load(data);
		renderTop();
	}).fail(function() {
		console.log( "error" );
	});
}

$(function() {
	JBread = $('#jbread');
	JList = $('#jlist');
	JDesc = $('#jdescription');

	JTree = new JavaTree();
	reload();
});
