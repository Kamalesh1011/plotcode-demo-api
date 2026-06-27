import { Octokit } from 'octokit';
import logger from './logger';

const token = process.env.GITHUB_TOKEN;
const org = process.env.GITHUB_ORG || 'plotcode';

let octokit: Octokit | null = null;
if (token) {
  octokit = new Octokit({ auth: token });
} else {
  logger.warn('GITHUB_TOKEN not set — GitHub integration disabled');
}

export function getOctokit(): Octokit {
  if (!octokit) throw new Error('GitHub not configured');
  return octokit;
}

export async function createBranch(repo: string, branch: string, baseSha: string): Promise<void> {
  const gh = getOctokit();
  await gh.rest.git.createRef({
    owner: org,
    repo,
    ref: `refs/heads/${branch}`,
    sha: baseSha
  });
}

export async function getDefaultBranchSha(repo: string, branch: string = 'main'): Promise<string> {
  const gh = getOctokit();
  const { data } = await gh.rest.git.getRef({
    owner: org,
    repo,
    ref: `heads/${branch}`
  });
  return (data as any).object.sha;
}

export async function createCommit(repo: string, branch: string, message: string, tree: string, parents: string[]): Promise<string> {
  const gh = getOctokit();
  const { data } = await gh.rest.git.createCommit({
    owner: org,
    repo,
    message,
    tree,
    parents
  });
  return data.sha;
}

export async function updateRef(repo: string, branch: string, sha: string): Promise<void> {
  const gh = getOctokit();
  await gh.rest.git.updateRef({
    owner: org,
    repo,
    ref: `heads/${branch}`,
    sha
  });
}

export async function createBlob(repo: string, content: string): Promise<string> {
  const gh = getOctokit();
  const { data } = await gh.rest.git.createBlob({
    owner: org,
    repo,
    content: Buffer.from(content).toString('base64'),
    encoding: 'base64'
  });
  return data.sha;
}

export async function createTree(repo: string, baseTree: string, files: Array<{ path: string; mode: "100644" | "100755" | "040000" | "160000" | "120000"; type: "tree" | "blob" | "commit"; sha: string }>): Promise<string> {
  const gh = getOctokit();
  const { data } = await gh.rest.git.createTree({
    owner: org,
    repo,
    base_tree: baseTree,
    tree: files
  });
  return data.sha;
}

export async function createPR(
  repo: string,
  title: string,
  head: string,
  base: string,
  body: string
): Promise<{ number: number; html_url: string }> {
  const gh = getOctokit();
  const { data } = await gh.rest.pulls.create({
    owner: org,
    repo,
    title,
    head,
    base,
    body
  });
  return { number: data.number, html_url: data.html_url };
}

export async function getPR(repo: string, prNumber: number): Promise<any> {
  const gh = getOctokit();
  const { data } = await gh.rest.pulls.get({ owner: org, repo, pull_number: prNumber });
  return data;
}

export async function mergePR(repo: string, prNumber: number, commitTitle?: string): Promise<string> {
  const gh = getOctokit();
  const { data } = await gh.rest.pulls.merge({
    owner: org,
    repo,
    pull_number: prNumber,
    commit_title: commitTitle
  });
  return (data as any).sha;
}

export async function getCIStatus(repo: string, ref: string): Promise<any> {
  const gh = getOctokit();
  const { data } = await gh.rest.checks.listForRef({ owner: org, repo, ref });
  return data;
}

export async function listRepoContents(repo: string, path: string, ref?: string): Promise<any[]> {
  const gh = getOctokit();
  const { data } = await gh.rest.repos.getContent({ owner: org, repo, path, ref });
  return Array.isArray(data) ? data : [data];
}

export async function getFileContent(repo: string, path: string, ref?: string): Promise<string> {
  const gh = getOctokit();
  const { data } = await gh.rest.repos.getContent({ owner: org, repo, path, ref });
  if (Array.isArray(data)) throw new Error('Path is a directory, not a file');
  if (data.type !== 'file') throw new Error('Not a file');
  return Buffer.from(data.content, 'base64').toString('utf-8');
}

export async function triggerWorkflow(repo: string, workflowId: string, ref: string, inputs?: Record<string, string>): Promise<void> {
  const gh = getOctokit();
  await gh.rest.actions.createWorkflowDispatch({
    owner: org,
    repo,
    workflow_id: workflowId,
    ref,
    inputs
  });
}

export { octokit };
